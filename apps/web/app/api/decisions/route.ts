import {getDecisionProviders, runDecisions, validateDecisionInput} from '@/lib/decision-runtime';
import {hasIntegrationSafeOrigin, isIntegrationAuthorized} from '@/lib/integration-runtime';
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
 * API route handler for decisions endpoints.
 *
 * @module route
 * @packageDocumentation
 */
const headers = {'Cache-Control': 'no-store'};
let active = 0;
/**
 * Function GET.
 *
 *
 * @example
 * ```typescript
 * import { GET } from './module';
 * ```
 */
export function GET() {
  return Response.json({providers: getDecisionProviders()}, {headers});
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
    return Response.json({error: 'Enter the private workspace execution token.'}, {status: 401, headers});
  }
  if (!request.headers.get('content-type')?.startsWith('application/json')) {
    return Response.json({error: 'JSON is required.'}, {status: 415, headers});
  }
  if (active >= 2) return Response.json({error: 'Two decision requests are running. Try again shortly.'}, {status: 429, headers});
  active++;
  try {
    if (!request.body) throw Error('A request is required.');
    const reader = request.body.getReader(), decoder = new TextDecoder();
    let text = '', bytes = 0;
    while (true) {
      const {done, value} = await reader.read();
      if (done) break;
      bytes += value.byteLength;
      if (bytes > 65536) { await reader.cancel(); throw Error('Request exceeds 64 KiB.'); }
      text += decoder.decode(value, {stream: true});
    }
    const input = validateDecisionInput(JSON.parse(text + decoder.decode()));
    const results = await runDecisions(input);
    return Response.json({results}, {headers});
  } catch (error) {
    // Only local validation errors reach this branch; upstream errors are normalized by the adapter.
    const message = error instanceof SyntaxError ? 'Invalid JSON request.' : error instanceof Error ? error.message : 'Decision request failed.';
    return Response.json({error: message.slice(0, 240)}, {status: 400, headers});
  } finally { active--; }
}
