import {executePlannedTask,hasIntegrationSafeOrigin,isIntegrationAuthorized} from '@/lib/integration-runtime';
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
 * API route handler for planned-tasks endpoints.
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
 if(active>=2)return Response.json({error:'Two planned tasks are already running in this web process.'},{status:429,headers});
 active++;
 let reader:ReadableStreamDefaultReader<Uint8Array>|null=null;
 const controller=new AbortController(),abort=()=>{controller.abort();void reader?.cancel().catch(()=>{});};
 request.signal.addEventListener('abort',abort,{once:true});if(request.signal.aborted)controller.abort();
 const timer=setTimeout(abort,45_000);
 try{
  reader=request.body.getReader();let text='',bytes=0;const decoder=new TextDecoder();
  while(true){const {done,value}=await reader.read();if(done)break;bytes+=value.byteLength;if(bytes>1024){await reader.cancel();throw Error('Request exceeds 1 KiB.');}text+=decoder.decode(value,{stream:true});}
  text+=decoder.decode();const body=JSON.parse(text);
  if(!body||Array.isArray(body)||typeof body!=='object'||Object.keys(body).length!==2||!Object.keys(body).every(key=>['runId','taskId'].includes(key))||![body.runId,body.taskId].every(value=>typeof value==='string'&&/^[a-zA-Z0-9_-]{1,128}$/.test(value)))throw Error('Only exact runId and taskId are accepted. Stored inputs cannot be overridden.');
  const result=await executePlannedTask(body.runId,body.taskId,process.env,controller.signal);
  return Response.json({result},{headers});
 }catch(error){const message=error instanceof Error?error.message:'Planned task failed.';return Response.json({error:message.replace(/\/(?:Users|private|tmp)\/[^\s]+/g,'[local path]').slice(0,350)},{status:400,headers});}
 finally{clearTimeout(timer);request.signal.removeEventListener('abort',abort);active--;}
}
