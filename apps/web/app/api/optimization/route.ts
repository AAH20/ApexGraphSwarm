import {assertJsonPrecision} from '@/lib/optimization-json';
import {optimizationOperation} from '@/lib/optimization-client';
import {hasIntegrationSafeOrigin,isIntegrationAuthorized} from '@/lib/integration-runtime';
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
 * API route handler for optimization endpoints.
 *
 * @module route
 * @packageDocumentation
 */
const headers={'Cache-Control':'no-store'};
let active=0;
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
export async function POST(request:Request){
 if(!isIntegrationAuthorized(request)||!hasIntegrationSafeOrigin(request))return Response.json({error:'Enter the private workspace execution token.'},{status:401,headers});
 if(!request.headers.get('content-type')?.startsWith('application/json'))return Response.json({error:'JSON is required.'},{status:415,headers});
 if(!request.body)return Response.json({error:'A request is required.'},{status:400,headers});
 if(active>=2)return Response.json({error:'Two local experiments are already running. Try again when one finishes.'},{status:429,headers});
 active++;
 try{
  const reader=request.body.getReader();let text='',bytes=0;const decoder=new TextDecoder();
  while(true){const {done,value}=await reader.read();if(done)break;bytes+=value.byteLength;if(bytes>131072){await reader.cancel();throw Error('Request exceeds 128 KiB.');}text+=decoder.decode(value,{stream:true});}
  text+=decoder.decode();const body=JSON.parse(text);assertJsonPrecision(body);
  if(!body||Array.isArray(body)||typeof body!=='object')throw Error('A JSON object is required.');
  if(!['schedule','evidence','waves','capacity','evaluate','telemetry','benchmark','evolve','compileDelegation','repositoryConflicts','verifyRepositoryConflicts'].includes(body.action))throw Error('Unsupported experiment.');
  return Response.json({result:await optimizationOperation(body)},{headers});
 }catch(error){const message=error instanceof Error?error.message:'Experiment failed.';return Response.json({error:message.replace(/\/(?:Users|private|tmp)\/[^\s]+/g,'[local path]').slice(0,300)},{status:400,headers});}
 finally{active--;}
}
