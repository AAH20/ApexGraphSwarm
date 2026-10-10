import {hasIntegrationSafeOrigin, isIntegrationAuthorized} from '../../../../lib/integration-runtime';
import {discoverMcpTools, getMcpDiscoveryCatalog, McpDiscoveryError} from '../../../../lib/mcp-discovery';

/**
 * Constant runtime.
 *
 *
 * @example
 * ```typescript
 * import { runtime } from './module';
 * ```
 */
export const runtime = 'nodejs';
/**
 * Constant dynamic.
 *
 *
 * @example
 * ```typescript
 * import { dynamic } from './module';
 * ```
 */
export const dynamic = 'force-dynamic';

/**
 * API route handler for ecosystem mcp endpoints.
 *
 * @module route
 * @packageDocumentation
 */
const headers = {'Cache-Control': 'no-store, max-age=0'};
const REQUEST_BYTES = 4096;

/**
 * Function GET.
 *
 *
 * @example
 * ```typescript
 * import { GET } from './module';
 * ```
 */
/**
 * API route handler for GET requests.
 *
 *
 * @example
 * ```typescript
 * import { GET } from './module';
 * ```
 */
export async function GET() {
  return Response.json(getMcpDiscoveryCatalog(), {headers});
}

/**
 * Function POST.
 *
 * @param {Request} request - Description of request.
 *
 * @example
 * ```typescript
 * const result = POST(...);
 * ```
 */
/**
 * API route handler for POST requests.
 *
 * @param {Request} request - Description of request.
 *
 * @example
 * ```typescript
 * const result = POST(...);
 * ```
 */
export async function POST(request: Request) {
  if (!isIntegrationAuthorized(request) || !hasIntegrationSafeOrigin(request)) {
    return Response.json({error: 'Unauthorized MCP discovery request.'}, {status: 401, headers});
  }
  if (!request.headers.get('content-type')?.toLowerCase().startsWith('application/json')) {
    return Response.json({error: 'Content-Type must be application/json.'}, {status: 415, headers});
  }
  if (!request.body) return Response.json({error: 'A request body is required.'}, {status: 400, headers});
  try {
    const declared = Number(request.headers.get('content-length') || 0);
    if (declared > REQUEST_BYTES) throw new McpDiscoveryError('MCP discovery request exceeds 4 KB.', 413);
    const reader = request.body.getReader();
    const chunks: Uint8Array[] = [];
    let total = 0;
    try {
      while (true) {
        const {done, value} = await reader.read();
        if (done) break;
        total += value.byteLength;
        if (total > REQUEST_BYTES) {
          await reader.cancel();
          throw new McpDiscoveryError('MCP discovery request exceeds 4 KB.', 413);
        }
        chunks.push(value);
      }
    } finally {
      reader.releaseLock();
    }
    const bytes = new Uint8Array(total);
    let offset = 0;
    for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength; }
    let body: unknown;
    try { body = JSON.parse(new TextDecoder().decode(bytes)); }
    catch { throw new McpDiscoveryError('Request body must be valid JSON.', 400); }
    if (!body || typeof body !== 'object' || Array.isArray(body) ||
        Object.keys(body).some(key => key !== 'serverId') || typeof (body as {serverId?: unknown}).serverId !== 'string') {
      throw new McpDiscoveryError('Request must contain only a configured serverId.', 400);
    }
    const result = await discoverMcpTools((body as {serverId: string}).serverId, {signal: request.signal});
    return Response.json(result, {headers});
  } catch (error) {
    const message = error instanceof McpDiscoveryError ? error.message : 'MCP discovery failed.';
    const status = error instanceof McpDiscoveryError ? error.status : 502;
    return Response.json({error: message}, {status, headers});
  }
}
