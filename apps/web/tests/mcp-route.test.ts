import assert from 'node:assert/strict';
import {createServer, type IncomingMessage, type ServerResponse} from 'node:http';
import test from 'node:test';
import {GET, POST} from '../app/api/ecosystem/mcp/route';

function readBody(request: IncomingMessage): Promise<string> {
  return new Promise((resolve, reject) => {
    let body = '';
    request.setEncoding('utf8');
    request.on('data', chunk => { body += chunk; });
    request.on('end', () => resolve(body));
    request.on('error', reject);
  });
}

function sendJson(response: ServerResponse, value: unknown, headers: Record<string, string> = {}) {
  response.writeHead(200, {'content-type': 'application/json', ...headers});
  response.end(JSON.stringify(value));
}

test('route performs a real loopback-only MCP handshake and protects discovery', async () => {
  const methods: string[] = [];
  const sessionId = 'loopback-fixture-session';
  const server = createServer(async (request, response) => {
    if (request.method === 'DELETE') {
      methods.push('DELETE');
      response.writeHead(200);
      response.end();
      return;
    }
    const message = JSON.parse(await readBody(request));
    methods.push(message.method);
    if (message.method === 'notifications/initialized') {
      response.writeHead(202);
      response.end();
      return;
    }
    if (message.method === 'initialize') {
      sendJson(response, {jsonrpc: '2.0', id: message.id, result: {
        protocolVersion: '2025-11-25', capabilities: {tools: {}}, serverInfo: {name: 'loopback fixture', version: '1'},
      }}, {'MCP-Session-Id': sessionId});
      return;
    }
    if (message.method === 'tools/list') {
      sendJson(response, {jsonrpc: '2.0', id: message.id, result: {
        tools: [{name: 'safe-read', description: 'Read-only fixture', inputSchema: {type: 'object', properties: {}}}],
      }});
      return;
    }
    response.writeHead(400);
    response.end();
  });

  const previous = {
    servers: process.env.MCP_SERVERS_JSON,
    token: process.env.MCP_SERVER_LOOPBACK_TEST_TOKEN,
    access: process.env.INTEGRATION_ACCESS_TOKEN,
  };
  try {
    await new Promise<void>((resolve, reject) => {
      server.once('error', reject);
      server.listen(0, '127.0.0.1', resolve);
    });
    const address = server.address();
    assert.ok(address && typeof address === 'object');
    const token = 'fixture-mcp-secret-value';
    process.env.MCP_SERVER_LOOPBACK_TEST_TOKEN = token;
    process.env.INTEGRATION_ACCESS_TOKEN = 'fixture-workbench-access-token';
    process.env.MCP_SERVERS_JSON = JSON.stringify([{
      id: 'loopback-fixture', label: 'Loopback MCP fixture',
      url: `http://127.0.0.1:${address.port}/mcp`, tokenEnv: 'MCP_SERVER_LOOPBACK_TEST_TOKEN',
    }]);

    const catalogResponse = await GET();
    assert.equal(catalogResponse.status, 200);
    const publicCatalog = await catalogResponse.json();
    assert.equal(JSON.stringify(publicCatalog).includes(String(address.port)), false);
    assert.equal(JSON.stringify(publicCatalog).includes(token), false);

    const unauthorized = await POST(new Request('http://127.0.0.1/api/ecosystem/mcp', {
      method: 'POST', headers: {'content-type': 'application/json'}, body: JSON.stringify({serverId: 'loopback-fixture'}),
    }));
    assert.equal(unauthorized.status, 401);

    const response = await POST(new Request('http://127.0.0.1/api/ecosystem/mcp', {
      method: 'POST', headers: {
        authorization: 'Bearer fixture-workbench-access-token',
        'content-type': 'application/json',
      }, body: JSON.stringify({serverId: 'loopback-fixture'}),
    }));
    assert.equal(response.status, 200, await response.clone().text());
    const discovery = await response.json();
    assert.equal(discovery.tools[0].name, 'safe-read');
    assert.deepEqual(methods, ['initialize', 'notifications/initialized', 'tools/list', 'DELETE']);

    const injectedUrl = await POST(new Request('http://127.0.0.1/api/ecosystem/mcp', {
      method: 'POST', headers: {
        authorization: 'Bearer fixture-workbench-access-token',
        'content-type': 'application/json',
      }, body: JSON.stringify({serverId: 'loopback-fixture', url: 'http://127.0.0.1/admin'}),
    }));
    assert.equal(injectedUrl.status, 400);
    assert.deepEqual(methods, ['initialize', 'notifications/initialized', 'tools/list', 'DELETE']);
  } finally {
    if (previous.servers === undefined) delete process.env.MCP_SERVERS_JSON;
    else process.env.MCP_SERVERS_JSON = previous.servers;
    if (previous.token === undefined) delete process.env.MCP_SERVER_LOOPBACK_TEST_TOKEN;
    else process.env.MCP_SERVER_LOOPBACK_TEST_TOKEN = previous.token;
    if (previous.access === undefined) delete process.env.INTEGRATION_ACCESS_TOKEN;
    else process.env.INTEGRATION_ACCESS_TOKEN = previous.access;
    await new Promise<void>(resolve => server.close(() => resolve()));
  }
});
