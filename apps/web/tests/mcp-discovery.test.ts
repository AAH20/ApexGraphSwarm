import assert from 'node:assert/strict';
import test from 'node:test';
import {discoverMcpTools, getMcpDiscoveryCatalog, McpDiscoveryError} from '../lib/mcp-discovery';

const session = 'opaque-session-42';
const secret = 'server-only-test-secret';
const profile = {id: 'fixture', label: 'Fixture MCP', url: 'https://mcp.example.test/mcp', tokenEnv: 'MCP_SERVER_FIXTURE_TOKEN'};
const env = {MCP_SERVERS_JSON: JSON.stringify([profile]), MCP_SERVER_FIXTURE_TOKEN: secret};

function rpc(id: number, result: unknown, options: {sessionId?: string; contentType?: string} = {}) {
  const headers = new Headers({'content-type': options.contentType ?? 'application/json'});
  if (options.sessionId) headers.set('MCP-Session-Id', options.sessionId);
  return new Response(JSON.stringify({jsonrpc: '2.0', id, result}), {status: 200, headers});
}

function tool(name: string) {
  return {name, title: `<${name}>`, description: 'untrusted description',
    inputSchema: {type: 'object', properties: {query: {type: 'string'}}, required: ['query']},
    annotations: {destructiveHint: true}, icons: [{src: 'https://untrusted.example/icon.svg'}]};
}

test('public catalog is non-secret and hides configured endpoint URLs', () => {
  const catalog = getMcpDiscoveryCatalog(env);
  assert.equal(catalog.servers.length, 1);
  assert.equal(catalog.servers[0].id, 'fixture');
  assert.equal(catalog.servers[0].configured, true);
  const serialized = JSON.stringify(catalog);
  assert.equal(serialized.includes(profile.url), false);
  assert.equal(serialized.includes(secret), false);
  assert.equal(getMcpDiscoveryCatalog({MCP_SERVERS_JSON: JSON.stringify([{...profile, tokenEnv: 'BAD_KEY'}])}).servers.length, 0);
});

test('initializes, negotiates session headers, paginates tools and deletes session', async () => {
  const calls: {method: string; body?: any; headers: Headers}[] = [];
  const fetcher: typeof fetch = async (_input, init) => {
    const headers = new Headers(init?.headers);
    const method = init?.method ?? 'GET';
    const body = init?.body ? JSON.parse(String(init.body)) : undefined;
    calls.push({method, body, headers});
    if (method === 'DELETE') return new Response(null, {status: 200});
    if (body?.method === 'initialize') return rpc(1, {
      protocolVersion: '2025-11-25', capabilities: {tools: {listChanged: true}, resources: {}},
      serverInfo: {name: 'fixture', version: '3.2', description: 'MCP server', websiteUrl: 'https://discarded.test'},
    }, {sessionId: session});
    if (body?.method === 'notifications/initialized') return new Response(null, {status: 202});
    if (body?.method === 'tools/list' && body.params.cursor === undefined) return rpc(body.id, {tools: [tool('alpha')], nextCursor: 'cursor-1'});
    if (body?.method === 'tools/list') return rpc(body.id, {tools: [tool('beta')]});
    return new Response(null, {status: 400});
  };

  const result = await discoverMcpTools('fixture', {env, fetcher});
  assert.deepEqual(result.tools.map(item => item.name), ['alpha', 'beta']);
  assert.equal(result.pagination.pages, 2);
  assert.equal(result.pagination.truncated, false);
  assert.deepEqual(result.server.serverInfo, {name: 'fixture', version: '3.2', description: 'MCP server'});
  assert.equal(JSON.stringify(result).includes('untrusted.example'), false);
  assert.equal(JSON.stringify(result).includes('annotations'), false);
  assert.deepEqual(calls.map(call => call.body?.method ?? call.method), [
    'initialize', 'notifications/initialized', 'tools/list', 'tools/list', 'DELETE',
  ]);
  assert.equal(calls[0].body.params.protocolVersion, '2025-11-25');
  assert.equal(calls[0].headers.has('MCP-Protocol-Version'), false);
  assert.equal(calls[0].headers.get('authorization'), `Bearer ${secret}`);
  assert.equal(calls[1].headers.get('MCP-Protocol-Version'), '2025-11-25');
  assert.equal(calls[1].headers.get('MCP-Session-Id'), session);
  assert.equal(calls[3].body.params.cursor, 'cursor-1');
  assert.equal(calls[4].headers.get('MCP-Session-Id'), session);
  assert.equal(calls.some(call => call.body?.method === 'tools/call'), false);
});

test('supports bounded SSE JSON-RPC response bodies', async () => {
  const methods: string[] = [];
  const fetcher: typeof fetch = async (_input, init) => {
    const body = init?.body ? JSON.parse(String(init.body)) : undefined;
    const method = init?.method ?? 'GET';
    methods.push(body?.method ?? method);
    if (method === 'DELETE') return new Response(null, {status: 405});
    if (body?.method === 'notifications/initialized') return new Response(null, {status: 202});
    const result = body.method === 'initialize'
      ? {protocolVersion: '2025-06-18', capabilities: {tools: {}}, serverInfo: {name: 'sse-fixture', version: '1'}}
      : {tools: [tool('sse-tool')]};
    const payload = `: priming comment\n\nevent: message\ndata: ${JSON.stringify({jsonrpc: '2.0', id: body.id, result})}\n\n`;
    const bodyStream = new ReadableStream<Uint8Array>({start(controller) { controller.enqueue(new TextEncoder().encode(payload)); controller.close(); }});
    return new Response(bodyStream, {status: 200, headers: {'content-type': 'text/event-stream; charset=utf-8'}});
  };
  const result = await discoverMcpTools('fixture', {env, fetcher});
  assert.equal(result.server.protocolVersion, '2025-06-18');
  assert.equal(result.tools[0].name, 'sse-tool');
  assert.equal(methods.includes('tools/list'), true);
  assert.equal(methods.includes('DELETE'), false, 'stateless server has no session to delete');
});

test('bounds pagination and rejects repeated cursors', async () => {
  const fetcher: typeof fetch = async (_input, init) => {
    const body = init?.body ? JSON.parse(String(init.body)) : undefined;
    if (body?.method === 'initialize') return rpc(1, {protocolVersion: '2025-11-25', capabilities: {tools: {}}, serverInfo: {name: 'loop', version: '1'}});
    if (body?.method === 'notifications/initialized') return new Response(null, {status: 202});
    return rpc(body.id, {tools: [], nextCursor: 'same-cursor'});
  };
  await assert.rejects(discoverMcpTools('fixture', {env, fetcher}),
    (error: unknown) => error instanceof McpDiscoveryError && /repeated a pagination cursor/.test(error.message));
});

test('reports truncation when a single response page exceeds the tool cap', async () => {
  const fetcher: typeof fetch = async (_input, init) => {
    const body = init?.body ? JSON.parse(String(init.body)) : undefined;
    if (init?.method === 'DELETE') return new Response(null, {status: 200});
    if (body?.method === 'notifications/initialized') return new Response(null, {status: 202});
    if (body?.method === 'initialize') return rpc(body.id, {
      protocolVersion: '2025-11-25', capabilities: {tools: {}}, serverInfo: {name: 'large-page', version: '1'},
    });
    if (body?.method === 'tools/list') return rpc(body.id, {tools: Array.from({length: 101}, (_, index) => tool(`tool-${index}`))});
    throw new Error('unexpected MCP request');
  };
  const result = await discoverMcpTools('fixture', {env, fetcher});
  assert.equal(result.tools.length, 100);
  assert.equal(result.pagination.truncated, true);
});

test('does not send notifications/cancelled while initialize is pending', async () => {
  const controller = new AbortController();
  const methods: string[] = [];
  const fetcher: typeof fetch = async (_input, init) => {
    const body = init?.body ? JSON.parse(String(init.body)) : undefined;
    methods.push(body?.method ?? init?.method ?? '');
    setTimeout(() => controller.abort(new Error('cancel init')), 0);
    return await new Promise<Response>((_resolve, reject) => {
      init?.signal?.addEventListener('abort', () => reject(new Error('fetch aborted')), {once: true});
    });
  };
  await assert.rejects(discoverMcpTools('fixture', {env, fetcher, signal: controller.signal}),
    (error: unknown) => error instanceof McpDiscoveryError && /cancelled/.test(error.message));
  assert.deepEqual(methods, ['initialize']);
});

test('rejects ambiguous JSON-RPC responses and unsafe schema keys', async () => {
  const ambiguous: typeof fetch = async (_input, init) => {
    const body = init?.body ? JSON.parse(String(init.body)) : undefined;
    if (body?.method === 'initialize') return new Response(JSON.stringify({
      jsonrpc: '2.0', id: body.id, result: {}, error: {code: -1, message: 'both'},
    }), {headers: {'content-type': 'application/json'}});
    throw new Error('unexpected MCP request');
  };
  await assert.rejects(discoverMcpTools('fixture', {env, fetcher: ambiguous}), /invalid JSON-RPC response/);

  const unsafeSchema: typeof fetch = async (_input, init) => {
    const body = init?.body ? JSON.parse(String(init.body)) : undefined;
    if (body?.method === 'initialize') return rpc(body.id, {
      protocolVersion: '2025-11-25', capabilities: {tools: {}}, serverInfo: {name: 'unsafe', version: '1'},
    });
    if (body?.method === 'notifications/initialized') return new Response(null, {status: 202});
    if (body?.method === 'tools/list') return rpc(body.id, {
      tools: [{name: 'unsafe', inputSchema: JSON.parse('{"type":"object","__proto__":{"polluted":true}}')}],
    });
    if (init?.method === 'DELETE') return new Response(null, {status: 200});
    throw new Error('unexpected MCP request');
  };
  await assert.rejects(discoverMcpTools('fixture', {env, fetcher: unsafeSchema}), /unsafe property name/);
});

test('cancels the pending MCP request and closes a stateful session on abort', async () => {
  const methods: string[] = [];
  const controller = new AbortController();
  const fetcher: typeof fetch = async (_input, init) => {
    const body = init?.body ? JSON.parse(String(init.body)) : undefined;
    const method = init?.method ?? 'GET';
    methods.push(body?.method ?? method);
    if (method === 'DELETE') return new Response(null, {status: 200});
    if (body?.method === 'initialize') return rpc(1, {protocolVersion: '2025-11-25', capabilities: {tools: {}}, serverInfo: {name: 'cancel-fixture', version: '1'}}, {sessionId: session});
    if (body?.method === 'notifications/initialized' || body?.method === 'notifications/cancelled') return new Response(null, {status: 202});
    if (body?.method === 'tools/list') {
      setTimeout(() => controller.abort(new Error('user cancelled')), 0);
      return await new Promise<Response>((_resolve, reject) => {
        init?.signal?.addEventListener('abort', () => reject(new Error('fetch aborted')), {once: true});
      });
    }
    throw new Error('unexpected request');
  };
  await assert.rejects(discoverMcpTools('fixture', {env, fetcher, signal: controller.signal}),
    (error: unknown) => error instanceof McpDiscoveryError && /cancelled/.test(error.message));
  assert.deepEqual(methods, ['initialize', 'notifications/initialized', 'tools/list', 'notifications/cancelled', 'DELETE']);
});

test('rejects arbitrary request fields, unknown profile IDs and unsafe profile endpoints', async () => {
  await assert.rejects(discoverMcpTools('fixture', {env: {MCP_SERVERS_JSON: JSON.stringify([{...profile, url: 'http://169.254.169.254/latest/meta-data'}])}}),
    (error: unknown) => error instanceof McpDiscoveryError && error.status === 503);
  await assert.rejects(discoverMcpTools('missing', {env}),
    (error: unknown) => error instanceof McpDiscoveryError && error.status === 404);
});
