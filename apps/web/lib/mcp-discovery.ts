import {isIP} from 'node:net';

export const MCP_DISCOVERY_LIMITS = {
  profiles: 8,
  timeoutMs: 20_000,
  cleanupTimeoutMs: 1_000,
  responseBytes: 1024 * 1024,
  tools: 100,
  pages: 5,
  schemaBytes: 32 * 1024,
} as const;

export const MCP_HANDSHAKE_VERSIONS = [
  '2025-11-25',
  '2025-06-18',
  '2025-03-26',
  '2024-11-05',
] as const;

type Env = Record<string, string | undefined>;
type McpProfile = {id: string; label: string; url: string; tokenEnv?: string; token?: string};
type McpHeaders = Record<string, string>;
type RpcResponse = {jsonrpc: '2.0'; id: string | number; result?: unknown; error?: {code: number; message: string}; transportSessionId?: string};
type SafeTool = {name: string; title?: string; description?: string; inputSchema: Record<string, unknown>};
type Fetcher = typeof fetch;

export class McpDiscoveryError extends Error {
  constructor(message: string, readonly status = 502) {
    super(message);
    this.name = 'McpDiscoveryError';
  }
}

function plainRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value && typeof value === 'object' && !Array.isArray(value));
}

function validId(value: unknown): value is string {
  return typeof value === 'string' && /^[a-z][a-z0-9-]{0,62}$/.test(value);
}

function endpoint(value: unknown): string | null {
  if (typeof value !== 'string' || value.length > 2048) return null;
  try {
    const url = new URL(value);
    const loopback = ['localhost', '127.0.0.1', '[::1]'].includes(url.hostname) ||
      (isIP(url.hostname) === 6 && url.hostname.toLowerCase() === '[::1]');
    if (url.username || url.password || url.search || url.hash) return null;
    if (url.protocol !== 'https:' && !(url.protocol === 'http:' && loopback)) return null;
    return url.toString();
  } catch {
    return null;
  }
}

function loadProfiles(env: Env): {profiles: McpProfile[]; error?: string} {
  const raw = env.MCP_SERVERS_JSON;
  if (!raw?.trim()) return {profiles: []};
  let parsed: unknown;
  try { parsed = JSON.parse(raw); } catch { return {profiles: [], error: 'MCP_SERVERS_JSON must be valid JSON.'}; }
  if (!Array.isArray(parsed) || parsed.length > MCP_DISCOVERY_LIMITS.profiles) {
    return {profiles: [], error: `MCP_SERVERS_JSON must be an array of at most ${MCP_DISCOVERY_LIMITS.profiles} profiles.`};
  }
  const ids = new Set<string>();
  const profiles: McpProfile[] = [];
  for (const row of parsed) {
    if (!plainRecord(row) || Object.keys(row).some(key => !['id', 'label', 'url', 'tokenEnv'].includes(key))) {
      return {profiles: [], error: 'An MCP profile contains unsupported fields.'};
    }
    if (!validId(row.id) || ids.has(row.id) || typeof row.label !== 'string' ||
        !row.label.trim() || row.label.length > 100) {
      return {profiles: [], error: 'An MCP profile has an invalid or duplicate id/label.'};
    }
    const url = endpoint(row.url);
    if (!url) return {profiles: [], error: `MCP profile ${row.id} must use a fixed HTTPS endpoint (loopback HTTP is allowed for local development).`};
    if (row.tokenEnv !== undefined && (typeof row.tokenEnv !== 'string' || !/^MCP_SERVER_[A-Z0-9_]{1,60}_TOKEN$/.test(row.tokenEnv))) {
      return {profiles: [], error: `MCP profile ${row.id} has an invalid token environment variable name.`};
    }
    const tokenEnv = row.tokenEnv as string | undefined;
    const token = tokenEnv ? env[tokenEnv] : undefined;
    if (token !== undefined && (token.length > 4096 || /[\r\n]/.test(token))) {
      return {profiles: [], error: `MCP profile ${row.id} has an invalid server credential.`};
    }
    profiles.push({id: row.id, label: row.label.trim(), url, tokenEnv, token});
    ids.add(row.id);
  }
  return {profiles};
}

export function getMcpDiscoveryCatalog(env: Env = process.env) {
  const loaded = loadProfiles(env);
  return {
    servers: loaded.profiles.map(profile => ({
      id: profile.id,
      label: profile.label,
      configured: !profile.tokenEnv || Boolean(profile.token),
      transport: 'streamable-http' as const,
      supportedProtocol: '2025-11-25' as const,
      statusText: profile.tokenEnv && !profile.token
        ? `Configure ${profile.tokenEnv} on the server.`
        : 'Fixed server-side profile; read-only tools discovery is available.',
    })),
    ...(loaded.error ? {configurationError: loaded.error} : {}),
  };
}

export async function discoverMcpTools(serverId: unknown, options: {
  env?: Env;
  fetcher?: Fetcher;
  signal?: AbortSignal;
  timeoutMs?: number;
} = {}) {
  if (!validId(serverId)) throw new McpDiscoveryError('A valid serverId is required.', 400);
  const env = options.env ?? process.env;
  const loaded = loadProfiles(env);
  if (loaded.error) throw new McpDiscoveryError('MCP server configuration is invalid.', 503);
  const profile = loaded.profiles.find(item => item.id === serverId);
  if (!profile) throw new McpDiscoveryError('MCP server profile is not configured.', 404);
  if (profile.tokenEnv && !profile.token) throw new McpDiscoveryError('MCP server credentials are not configured.', 503);

  const fetcher = options.fetcher ?? fetch;
  const controller = new AbortController();
  let timedOut = false;
  const abortFromCaller = () => controller.abort(options.signal?.reason);
  if (options.signal?.aborted) abortFromCaller();
  else options.signal?.addEventListener('abort', abortFromCaller, {once: true});
  const timeout = setTimeout(() => {
    timedOut = true;
    controller.abort(new Error('MCP discovery timed out.'));
  }, options.timeoutMs ?? MCP_DISCOVERY_LIMITS.timeoutMs);

  let sessionId: string | undefined;
  let protocolVersion: string | undefined;
  let activeRequestId: number | undefined;
  let activeMethod: string | undefined;
  let nextRequestId = 1;
  const baseHeaders: McpHeaders = {
    'content-type': 'application/json',
    accept: 'application/json, text/event-stream',
    ...(profile.token ? {authorization: `Bearer ${profile.token}`} : {}),
  };

  const send = async (message: Record<string, unknown>, method: string, id?: number, cleanup = false) => {
    const headers: McpHeaders = {...baseHeaders};
    if (protocolVersion) headers['MCP-Protocol-Version'] = protocolVersion;
    if (sessionId) headers['MCP-Session-Id'] = sessionId;
    const signal = cleanup ? AbortSignal.timeout(MCP_DISCOVERY_LIMITS.cleanupTimeoutMs) : controller.signal;
    const response = await fetcher(profile.url, {
      method: 'POST', headers, body: JSON.stringify(message), signal,
      redirect: 'error', cache: 'no-store',
    });
    if (!id) {
      if (![200, 202, 204].includes(response.status)) {
        await response.body?.cancel().catch(() => undefined);
        throw new McpDiscoveryError(`MCP server rejected ${method} (HTTP ${response.status}).`);
      }
      await response.body?.cancel().catch(() => undefined);
      return undefined;
    }
    if (!response.ok) {
      await response.body?.cancel().catch(() => undefined);
      throw new McpDiscoveryError(`MCP server rejected ${method} (HTTP ${response.status}).`);
    }
    const headerSession = response.headers.get('mcp-session-id');
    if (headerSession !== null) {
      if (!headerSession.length || headerSession.length > 1024 || /[^\x21-\x7e]/.test(headerSession)) {
        await response.body?.cancel().catch(() => undefined);
        throw new McpDiscoveryError('MCP server returned an invalid session header.');
      }
      if (method === 'initialize') sessionId = headerSession;
    }
    const rpc = await readRpc(response, id, method);
    if (headerSession !== null) {
      rpc.transportSessionId = headerSession;
    }
    return rpc;
  };

  const request = async (method: string, params: Record<string, unknown>, cleanup = false) => {
    const id = nextRequestId++;
    activeRequestId = id;
    activeMethod = method;
    const response = await send({jsonrpc: '2.0', id, method, params}, method, id, cleanup) as RpcResponse;
    activeRequestId = undefined;
    activeMethod = undefined;
    if (response.error) throw new McpDiscoveryError(`MCP server returned an error for ${method} (${response.error.code}).`);
    if (!('result' in response)) throw new McpDiscoveryError(`MCP server returned no result for ${method}.`);
    return {result: response.result, transportSessionId: response.transportSessionId};
  };

  try {
    const initializeReply = await request('initialize', {
      protocolVersion: MCP_HANDSHAKE_VERSIONS[0],
      capabilities: {},
      clientInfo: {name: 'ApexGraphSwarm', version: '0.1.0'},
    });
    sessionId = initializeReply.transportSessionId;
    const initialized = initializeReply.result;
    if (!plainRecord(initialized) || typeof initialized.protocolVersion !== 'string' ||
        !(MCP_HANDSHAKE_VERSIONS as readonly string[]).includes(initialized.protocolVersion)) {
      throw new McpDiscoveryError('MCP server negotiated an unsupported handshake protocol version.');
    }
    protocolVersion = initialized.protocolVersion;
    if (!plainRecord(initialized.capabilities) || !plainRecord(initialized.capabilities.tools)) {
      throw new McpDiscoveryError('MCP server returned invalid tool capability metadata.');
    }
    const serverInfo = safeServerInfo(initialized.serverInfo);
    // Servers may choose stateless HTTP and omit a session ID. Stateful servers
    // return MCP-Session-Id from the initialize response.
    const initializedNotification = await send({jsonrpc: '2.0', method: 'notifications/initialized'}, 'notifications/initialized');
    void initializedNotification;

    const tools: SafeTool[] = [];
    const cursors = new Set<string>();
    let cursor: string | undefined;
    let clippedInPage = false;
    let pages = 0;
    do {
      if (pages >= MCP_DISCOVERY_LIMITS.pages || tools.length >= MCP_DISCOVERY_LIMITS.tools) break;
      const page = await request('tools/list', cursor ? {cursor} : {});
      const result = page.result;
      if (!plainRecord(result) || !Array.isArray(result.tools)) throw new McpDiscoveryError('MCP server returned an invalid tools/list result.');
      if (result.tools.length > MCP_DISCOVERY_LIMITS.tools - tools.length) clippedInPage = true;
      for (const tool of result.tools) {
        if (tools.length >= MCP_DISCOVERY_LIMITS.tools) break;
        tools.push(sanitizeTool(tool));
      }
      pages += 1;
      if (result.nextCursor === undefined || result.nextCursor === null || result.nextCursor === '') {
        cursor = undefined;
      } else {
        if (typeof result.nextCursor !== 'string' || result.nextCursor.length > 2048) {
          throw new McpDiscoveryError('MCP server returned an invalid pagination cursor.');
        }
        if (cursors.has(result.nextCursor)) throw new McpDiscoveryError('MCP server repeated a pagination cursor.');
        cursors.add(result.nextCursor);
        cursor = result.nextCursor;
      }
    } while (cursor && tools.length < MCP_DISCOVERY_LIMITS.tools && pages < MCP_DISCOVERY_LIMITS.pages);

    return {
      server: {id: profile.id, label: profile.label, protocolVersion, serverInfo,
        capabilities: sanitizeCapabilities(initialized.capabilities)},
      tools,
      pagination: {pages, truncated: Boolean(cursor) || clippedInPage},
    };
  } catch (error) {
    if (controller.signal.aborted && activeRequestId !== undefined && activeMethod && activeMethod !== 'initialize') {
      await send({jsonrpc: '2.0', method: 'notifications/cancelled',
        params: {requestId: activeRequestId, reason: timedOut ? 'Discovery timeout.' : 'Discovery cancelled.'}},
      'notifications/cancelled', undefined, true).catch(() => undefined);
    }
    if (error instanceof McpDiscoveryError) throw error;
    if (controller.signal.aborted) {
      throw new McpDiscoveryError(timedOut ? 'MCP discovery exceeded its time limit.' : 'MCP discovery was cancelled.', 504);
    }
    throw new McpDiscoveryError('MCP discovery failed; verify the configured endpoint and credentials.');
  } finally {
    clearTimeout(timeout);
    options.signal?.removeEventListener('abort', abortFromCaller);
    if (sessionId) {
      const headers: McpHeaders = {...baseHeaders, 'MCP-Session-Id': sessionId};
      if (protocolVersion) headers['MCP-Protocol-Version'] = protocolVersion;
      try {
        const response = await fetcher(profile.url, {method: 'DELETE', headers,
          signal: AbortSignal.timeout(MCP_DISCOVERY_LIMITS.cleanupTimeoutMs),
          redirect: 'error', cache: 'no-store'});
        await response.body?.cancel().catch(() => undefined);
      } catch { /* Session cleanup is best effort; never mask discovery output. */ }
    }
  }

}

async function readRpc(response: Response, expectedId: number, method: string): Promise<RpcResponse> {
  const contentType = response.headers.get('content-type')?.split(';', 1)[0].trim().toLowerCase();
  let text: string;
  if (contentType === 'application/json') {
    text = await readBoundedText(response, MCP_DISCOVERY_LIMITS.responseBytes);
    let value: unknown;
    try { value = JSON.parse(text); } catch { throw new McpDiscoveryError(`MCP server returned invalid JSON for ${method}.`); }
    return validateRpc(value, expectedId, method);
  }
  if (contentType === 'text/event-stream') return readSseRpc(response, expectedId, method);
  await response.body?.cancel().catch(() => undefined);
  throw new McpDiscoveryError(`MCP server returned an unsupported response type for ${method}.`);
}

function validateRpc(value: unknown, expectedId: number, method: string): RpcResponse {
  const hasResult = plainRecord(value) && Object.hasOwn(value, 'result');
  const hasError = plainRecord(value) && Object.hasOwn(value, 'error');
  if (!plainRecord(value) || value.jsonrpc !== '2.0' || value.id !== expectedId ||
      hasResult === hasError ||
      (value.error !== undefined && (!plainRecord(value.error) || typeof value.error.code !== 'number' || typeof value.error.message !== 'string'))) {
    throw new McpDiscoveryError(`MCP server returned an invalid JSON-RPC response for ${method}.`);
  }
  return value as RpcResponse;
}

async function readBoundedText(response: Response, maximum: number): Promise<string> {
  if (!response.body) throw new McpDiscoveryError('MCP server returned an empty response.');
  const reader = response.body.getReader();
  const chunks: Uint8Array[] = [];
  let total = 0;
  try {
    while (true) {
      const {done, value} = await reader.read();
      if (done) break;
      total += value.byteLength;
      if (total > maximum) throw new McpDiscoveryError('MCP response exceeded the 1 MiB limit.');
      chunks.push(value);
    }
  } catch (error) {
    await reader.cancel().catch(() => undefined);
    throw error;
  } finally {
    reader.releaseLock();
  }
  const bytes = new Uint8Array(total);
  let offset = 0;
  for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength; }
  return new TextDecoder().decode(bytes);
}

async function readSseRpc(response: Response, expectedId: number, method: string): Promise<RpcResponse> {
  if (!response.body) throw new McpDiscoveryError('MCP server returned an empty SSE stream.');
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let pending = '';
  let total = 0;
  const inspect = (event: string): RpcResponse | undefined => {
    const data = event.split(/\r?\n/).filter(line => line.startsWith('data:')).map(line => line.slice(5).replace(/^ /, '')).join('\n');
    if (!data.trim()) return undefined;
    let message: unknown;
    try { message = JSON.parse(data); } catch { throw new McpDiscoveryError(`MCP server sent invalid SSE JSON for ${method}.`); }
    if (!plainRecord(message) || message.id !== expectedId) return undefined;
    return validateRpc(message, expectedId, method);
  };
  try {
    while (true) {
      const {done, value} = await reader.read();
      if (done) break;
      total += value.byteLength;
      if (total > MCP_DISCOVERY_LIMITS.responseBytes) throw new McpDiscoveryError('MCP SSE response exceeded the 1 MiB limit.');
      pending += decoder.decode(value, {stream: true});
      let boundary = pending.search(/\r?\n\r?\n/);
      while (boundary >= 0) {
        const event = pending.slice(0, boundary);
        const separator = pending.slice(boundary).match(/^\r?\n\r?\n/)?.[0] ?? '\n\n';
        pending = pending.slice(boundary + separator.length);
        const rpc = inspect(event);
        if (rpc) return rpc;
        boundary = pending.search(/\r?\n\r?\n/);
      }
    }
    pending += decoder.decode();
    const final = inspect(pending);
    if (final) return final;
    throw new McpDiscoveryError(`MCP SSE stream ended without a response for ${method}.`);
  } finally {
    await reader.cancel().catch(() => undefined);
    reader.releaseLock();
  }
}

function safeServerInfo(value: unknown) {
  if (!plainRecord(value) || typeof value.name !== 'string' || typeof value.version !== 'string') {
    throw new McpDiscoveryError('MCP server returned invalid serverInfo.');
  }
  return {name: value.name.slice(0, 100), version: value.version.slice(0, 100),
    ...(typeof value.title === 'string' ? {title: value.title.slice(0, 200)} : {}),
    ...(typeof value.description === 'string' ? {description: value.description.slice(0, 1000)} : {})};
}

function sanitizeCapabilities(value: unknown) {
  if (!plainRecord(value)) return {};
  const tools = plainRecord(value.tools) ? {tools: {listChanged: value.tools.listChanged === true}} : {};
  return tools;
}

function sanitizeSchema(value: unknown): Record<string, unknown> {
  if (!plainRecord(value)) throw new McpDiscoveryError('MCP tool inputSchema must be an object.');
  let visited = 0;
  const copy = (item: unknown, depth: number): unknown => {
    visited += 1;
    if (visited > 2000 || depth > 16) throw new McpDiscoveryError('MCP tool schema exceeds structural limits.');
    if (item === null || typeof item === 'boolean') return item;
    if (typeof item === 'number') {
      if (!Number.isFinite(item)) throw new McpDiscoveryError('MCP tool schema contains a non-finite number.');
      return item;
    }
    if (typeof item === 'string') return item.slice(0, 4096);
    if (Array.isArray(item)) {
      if (item.length > 200) throw new McpDiscoveryError('MCP tool schema has too many array entries.');
      return item.map(child => copy(child, depth + 1));
    }
    if (!plainRecord(item)) throw new McpDiscoveryError('MCP tool schema contains an unsupported value.');
    const entries = Object.entries(item);
    if (entries.length > 200) throw new McpDiscoveryError('MCP tool schema has too many properties.');
    const out: Record<string, unknown> = Object.create(null);
    for (const [key, child] of entries) {
      if (key.length > 128 || ['__proto__', 'constructor', 'prototype'].includes(key)) {
        throw new McpDiscoveryError('MCP tool schema contains an unsafe property name.');
      }
      out[key] = copy(child, depth + 1);
    }
    return out;
  };
  const result = copy(value, 0) as Record<string, unknown>;
  if (new TextEncoder().encode(JSON.stringify(result)).length > MCP_DISCOVERY_LIMITS.schemaBytes) {
    throw new McpDiscoveryError('MCP tool inputSchema exceeded the 32 KiB limit.');
  }
  return result;
}

function sanitizeTool(value: unknown): SafeTool {
  if (!plainRecord(value) || typeof value.name !== 'string' || !value.name.trim() || value.name.length > 128) {
    throw new McpDiscoveryError('MCP server returned an invalid tool entry.');
  }
  return {
    name: value.name,
    ...(typeof value.title === 'string' ? {title: value.title.slice(0, 200)} : {}),
    ...(typeof value.description === 'string' ? {description: value.description.slice(0, 1000)} : {}),
    inputSchema: sanitizeSchema(value.inputSchema),
  };
}
