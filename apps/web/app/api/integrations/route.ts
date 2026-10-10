import {NextResponse} from 'next/server';
import {hasIntegrationSafeOrigin,isIntegrationAuthorized,INTEGRATION_LIMITS} from '@/lib/integration-runtime';
import {integrationRuntime} from '@/lib/integration-runtime-instance';
import {ExecutionRequestConflictError,ExecutionRequestRecoveryError,startIdempotentIntegrationRequest} from '@/lib/execution-request-client';

/**
 * Constant runtime.
 *
 *
 * @example
 * ```typescript
 * import { runtime } from './module';
 * ```
 */
export const runtime='nodejs';
/**
 * Constant dynamic.
 *
 *
 * @example
 * ```typescript
 * import { dynamic } from './module';
 * ```
 */
export const dynamic='force-dynamic';

/**
 * API route handler for integrations endpoints.
 *
 * @module route
 * @packageDocumentation
 */
const noStore={'Cache-Control':'no-store, max-age=0'};
/**
 * Function authorized.
 *
 * @param {Request} request - Description of request.
 *
 * @example
 * ```typescript
 * const result = authorized(...);
 * ```
 */
function authorized(request:Request){return isIntegrationAuthorized(request)&&hasIntegrationSafeOrigin(request);}
/**
 * Function readJson.
 *
 * @param {Request} request - Description of request.
 *
 * @example
 * ```typescript
 * const result = readJson(...);
 * ```
 */
async function readJson(request:Request){const declared=Number(request.headers.get('content-length')||0);if(declared>INTEGRATION_LIMITS.requestBytes)throw new Error('Integration request exceeds the 2 MB limit.');if(!request.body)throw new Error('Request body is required.');const reader=request.body.getReader(),chunks:Uint8Array[]=[];let total=0;while(true){const {done,value}=await reader.read();if(done)break;total+=value.byteLength;if(total>INTEGRATION_LIMITS.requestBytes){await reader.cancel();throw new Error('Integration request exceeds the 2 MB limit.');}chunks.push(value);}const bytes=new Uint8Array(total);let offset=0;for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.length;}try{return JSON.parse(new TextDecoder().decode(bytes));}catch{throw new Error('Request body must be valid JSON.');}}

/**
 * Function GET.
 *
 * @param {Request} _request - Description of _request.
 *
 * @example
 * ```typescript
 * const result = GET(...);
 * ```
 */
/**
 * API route handler for GET requests.
 *
 * @param {Request} _request - Description of _request.
 *
 * @example
 * ```typescript
 * const result = GET(...);
 * ```
 */
export async function GET(_request:Request){return NextResponse.json({integrations:integrationRuntime.catalog(),limits:{requestBytes:INTEGRATION_LIMITS.requestBytes,concurrency:INTEGRATION_LIMITS.concurrency,queue:INTEGRATION_LIMITS.queued,timeoutMs:INTEGRATION_LIMITS.timeoutMs,kernelNodes:INTEGRATION_LIMITS.kernelNodes,kernelEdges:INTEGRATION_LIMITS.kernelEdges,modelNodes:INTEGRATION_LIMITS.modelInputNodes,modelEdges:INTEGRATION_LIMITS.modelInputEdges}},{headers:noStore});}

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
export async function POST(request:Request){if(!authorized(request))return NextResponse.json({error:'Unauthorized integration request.'},{status:401,headers:noStore});if(!request.headers.get('content-type')?.toLowerCase().startsWith('application/json'))return NextResponse.json({error:'Content-Type must be application/json.'},{status:415,headers:noStore});const idempotencyKey=request.headers.get('idempotency-key');if(!idempotencyKey)return NextResponse.json({error:'Idempotency-Key header is required.'},{status:400,headers:noStore});try{const payload=await readJson(request),authorization=request.headers.get('authorization')!,started=await startIdempotentIntegrationRequest({idempotencyKey,scopeToken:authorization.slice(7),payload,env:process.env,findJob:jobId=>integrationRuntime.get(jobId),startJob:(value,jobId)=>integrationRuntime.startRegistered(value,jobId)});if(started.recoveryRequired)return NextResponse.json({error:'Execution recovery is required; automatic redispatch was refused.',recovery:{jobId:started.jobId,runId:started.runId,durableRunIdempotencyKey:started.durableRunIdempotencyKey,lookup:'Inspect this durable control run before deciding whether a retry is safe.'}},{status:409,headers:noStore});return NextResponse.json({job:started.job},{status:202,headers:noStore});}catch(error){const message=error instanceof Error?error.message:'Invalid integration request.';if(error instanceof ExecutionRequestRecoveryError)return NextResponse.json({error:message,recovery:{jobId:error.jobId,runId:error.runId,durableRunIdempotencyKey:`integration-${error.jobId}`}},{status:409,headers:noStore});const status=error instanceof ExecutionRequestConflictError?409:/unknown integration|not configured|not allowlisted|is not supported|is required|must |exceeds|limited|invalid|expected|snapshot|not an allowed|not supported|must contain|must be/i.test(message)?400:503;return NextResponse.json({error:message},{status,headers:noStore});}}
