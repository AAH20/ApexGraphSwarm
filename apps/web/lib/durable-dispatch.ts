import {execFile} from 'node:child_process';
import {randomUUID} from 'node:crypto';
import {mkdir} from 'node:fs/promises';
import path from 'node:path';
import {assertJsonPrecision} from './optimization-json';

/**
 * Core library module for durable dispatch.ts functionality.
 *
 * @module durable-dispatch
 * @packageDocumentation
 */
/**
 * Type Env.
 *
 *
 * @example
 * ```typescript
 * import { Env } from './module';
 * ```
 */
type Env=Record<string,string|undefined>;
/**
 * Type DispatchPolicy.
 *
 *
 * @example
 * ```typescript
 * import { DispatchPolicy } from './module';
 * ```
 */
export type DispatchPolicy={integrationId:string;operation:string;resourceId:string;maxCostMicrousd:number;maxProviderCalls?:number;modelId?:string;parameterEquals?:Record<string,string|number>};
/**
 * Type DispatchContext.
 *
 *
 * @example
 * ```typescript
 * import { DispatchContext } from './module';
 * ```
 */
export type DispatchContext={begin:(provider:string,model:string)=>Promise<string>;record:(id:string,evidence:Record<string,unknown>)=>Promise<void>;signal:AbortSignal};
/**
 * Type DispatchResult.
 *
 *
 * @example
 * ```typescript
 * import { DispatchResult } from './module';
 * ```
 */
export type DispatchResult={result:unknown;usage?:{inputTokens:number|null;outputTokens:number|null};externalCancel?:()=>Promise<void>};
/**
 * Type GovernedDispatch.
 *
 *
 * @example
 * ```typescript
 * import { GovernedDispatch } from './module';
 * ```
 */
export type GovernedDispatch=(integrationId:string,operation:string,parameters:Record<string,string|number>,env:Env,signal:AbortSignal,jobId:string,invoke:(context:DispatchContext)=>Promise<DispatchResult>)=>Promise<DispatchResult>;
const isRecord=(v:unknown):v is Record<string,unknown>=>!!v&&typeof v==='object'&&!Array.isArray(v);
const identifier=(v:unknown)=>typeof v==='string'&&v.length>0&&v.length<=128&&!/[\x00-\x1f]/.test(v);
/**
 * Function dispatchPolicy.
 *
 * @param {string} integrationId - Description of integrationId.
 * @param {string} operation - Description of operation.
 * @param {Record<string,string|number>} parameters - Description of parameters.
 * @param {Env} env - Description of env.
 * @returns {DispatchPolicy} Description of return value.
 *
 * @example
 * ```typescript
 * const result = dispatchPolicy(..., ..., ..., ...);
 * ```
 */
export function dispatchPolicy(integrationId:string,operation:string,parameters:Record<string,string|number>,env:Env):DispatchPolicy{
 if(!env.APEX_WORKER_CREDENTIAL||!identifier(env.APEX_WORKER_ID))throw Error('External execution requires an enrolled APEX_WORKER_ID and APEX_WORKER_CREDENTIAL and exact capability grants.');
 let policies:unknown;try{policies=JSON.parse(env.APEX_INTEGRATION_POLICIES_JSON||'[]');}catch{throw Error('APEX_INTEGRATION_POLICIES_JSON must be valid JSON.');}
 if(!Array.isArray(policies)||policies.length>100)throw Error('At most 100 integration policies are supported.');
 const matching=policies.filter(value=>isRecord(value)&&value.integrationId===integrationId&&value.operation===operation);
 if(matching.length!==1)throw Error('Exactly one server policy must authorize this integration and operation.');
 const policy=matching[0] as DispatchPolicy;
 if(!identifier(policy.resourceId)||!Number.isSafeInteger(policy.maxCostMicrousd)||policy.maxCostMicrousd<0)throw Error('The server policy needs an exact resource ID and integer nonnegative cost reservation.');
 if(policy.parameterEquals!==undefined&&!isRecord(policy.parameterEquals))throw Error('Policy parameterEquals must be an object.');
 if(policy.maxProviderCalls!==undefined&&(!Number.isSafeInteger(policy.maxProviderCalls)||policy.maxProviderCalls<1||policy.maxProviderCalls>6))throw Error('Policy maxProviderCalls must be between 1 and 6.');
 const outputCap=integrationId==='ai-gateway'?1000:600;
 if(parameters.maxOutputTokens!==undefined&&(!Number.isSafeInteger(parameters.maxOutputTokens)||Number(parameters.maxOutputTokens)<1||Number(parameters.maxOutputTokens)>outputCap))throw Error(`Output must be bounded to at most ${outputCap} tokens per call.`);
 const fixed=policy.parameterEquals||{};
 for(const [key,value] of Object.entries(parameters))if(key!=='maxOutputTokens'&&fixed[key]!==value)throw Error('Integration parameters do not match the server capability policy.');
 for(const [key,value] of Object.entries(fixed))if(parameters[key]!==value)throw Error('A required capability parameter does not match the server policy.');
 if(['harness','openmanus','understand-anything'].includes(integrationId)&&(!fixed.harnessId||!fixed.authMode))throw Error('Harness policies must pin harnessId and authMode.');
 if(['openrouter','vllm','ai-gateway'].includes(integrationId)&&policy.modelId!==env[integrationId==='openrouter'?'OPENROUTER_MODEL':integrationId==='vllm'?'VLLM_MODEL':'GRAPH_REVIEW_MODEL'])throw Error('The policy must pin the configured model ID.');
 return policy;
}

/**
 * Function pythonJson.
 *
 * @param {string} module - Description of module.
 * @param {Record<string,unknown>} input - Description of input.
 * @param {Env} env - Description of env.
 * @returns {Promise<Record<string,any>>} Description of return value.
 *
 * @example
 * ```typescript
 * const result = pythonJson(..., ..., ...);
 * ```
 */
async function pythonJson(module:string,input:Record<string,unknown>,env:Env):Promise<Record<string,any>>{
 return new Promise((resolve,reject)=>{
  const child=execFile('python3',['-m',module],{cwd:path.resolve(process.cwd(),'../..'),timeout:10000,maxBuffer:2*1024*1024,encoding:'utf8',env:{NODE_ENV:process.env.NODE_ENV||'production',PATH:env.PATH||process.env.PATH,LANG:'C.UTF-8',PYTHONIOENCODING:'utf-8',PYTHONDONTWRITEBYTECODE:'1'}},(error,stdout)=>{
   try{const result=JSON.parse(stdout);if(error||result.error)reject(Error(result.error||'Durable operation failed.'));else{assertJsonPrecision(result);resolve(result);}}catch{reject(Error('Durable operation returned invalid bounded JSON.'));}
  });child.stdin?.on('error',()=>{});child.stdin?.end(JSON.stringify(input));
 });
}
/**
 * Function durableOperation.
 *
 * @param {Record<string,unknown>} input - Description of input.
 * @param {Env} env - Description of env.
 *
 * @example
 * ```typescript
 * const result = durableOperation(..., ...);
 * ```
 */
export async function durableOperation(input:Record<string,unknown>,env:Env=process.env){
 const directory=env.APEX_CONTROL_DB_PATH?path.dirname(path.resolve(env.APEX_CONTROL_DB_PATH)):path.resolve(process.cwd(),'../../.runtime');
 await mkdir(directory,{recursive:true,mode:0o700});
 const dbPath=env.APEX_CONTROL_DB_PATH?path.resolve(env.APEX_CONTROL_DB_PATH):path.join(directory,'control.sqlite');
 const response=await pythonJson('apexgraphswarm.control',{...input,dbPath},env);if(!isRecord(response.data))throw Error('Durable operation returned no data.');return response.data as Record<string,any>;
}
/**
 * Function normalizeProviderReceipt.
 *
 * @param {Record<string,unknown>} payload - Description of payload.
 * @param {string} model - Description of model.
 * @param {Env} env - Description of env.
 *
 * @example
 * ```typescript
 * const result = normalizeProviderReceipt(..., ..., ...);
 * ```
 */
export async function normalizeProviderReceipt(payload:Record<string,unknown>,model:string,env:Env){
 const result=await pythonJson('apexgraphswarm.provider_receipts',{action:'normalizeOpenRouter',payload,expectedGenerationId:payload.id,expectedModel:model},env);if(result.provider!=='openrouter'||typeof result.costMicrousd!=='number')throw Error('Provider receipt was not normalized.');return result;
}
/**
 * Function sanitize.
 *
 * @param value - Description of value.
 * @param {Env} env - Description of env.
 * @returns {unknown} Description of return value.
 *
 * @example
 * ```typescript
 * const result = sanitize(..., ...);
 * ```
 */
function sanitize(value:unknown,env:Env):unknown{
 const secrets=Object.entries(env).filter(([key,v])=>/(?:KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL)$/i.test(key)&&v&&v.length>=8).map(([,v])=>v!);
 if(typeof value==='string')return secrets.reduce((text,secret)=>text.split(secret).join('[redacted]'),value);
 if(Array.isArray(value))return value.map(v=>sanitize(v,env));
 if(isRecord(value))return Object.fromEntries(Object.entries(value).filter(([key])=>!/(?:api_?key|access_?token|secret|password|authorization|credential)$/i.test(key)).map(([key,v])=>[key,sanitize(v,env)]));
 return value;
}
/**
 * Constant withDurableDispatch.
 *
 *
 * @example
 * ```typescript
 * import { withDurableDispatch } from './module';
 * ```
 */
export const withDurableDispatch:GovernedDispatch=async(integrationId,operation,parameters,env,signal,jobId,invoke)=>{
 const policy=dispatchPolicy(integrationId,operation,parameters,env),credential=env.APEX_WORKER_CREDENTIAL!;
 const created=await durableOperation({action:'create',idempotencyKey:`integration-${jobId}`,budgetMicrousd:policy.maxCostMicrousd,plan:{version:1,agents:[{id:'adapter',name:'Authenticated integration worker'}],tasks:[{id:'execute',agentId:'adapter',dependencies:[],executionClass:'external',maxAttempts:1,reservedCostMicrousd:policy.maxCostMicrousd,tool:`integration:${integrationId}:${operation}`,resource:policy.resourceId,payload:{jobId,integrationId,operation}}]}},env);
 const runId=created.run.id;
 if(signal.aborted){await durableOperation({action:'cancel',runId},env);throw Error('Cancelled before dispatch.');}
 const claimed=await durableOperation({action:'authClaim',runId,workerId:env.APEX_WORKER_ID,credential,leaseSeconds:60},env);
 if(!claimed.task)throw Error('This durable task is not claimable; inspect its persisted state before retrying.');
 return withClaimedTaskDispatch(claimed.task,runId,policy,env,signal,invoke);
};

async function withClaimedTaskDispatch(task:Record<string,any>,runId:string,policy:DispatchPolicy,env:Env,signal:AbortSignal,invoke:(context:DispatchContext)=>Promise<DispatchResult>):Promise<DispatchResult>{
 const credential=env.APEX_WORKER_CREDENTIAL!,operation=policy.operation;
 const common={credential,taskId:task.taskId,leaseToken:task.leaseToken};
 const controller=new AbortController(),abort=()=>controller.abort();signal.addEventListener('abort',abort,{once:true});if(signal.aborted)controller.abort();
 // Admission reservations bound planned fan-out, not the provider's eventual charge.
 const maxCalls=policy.maxProviderCalls??(operation==='delegate'||operation==='swarm'?3:1);
 const callReservation=Math.floor(policy.maxCostMicrousd/maxCalls);
 const calls=new Map<string,number|null>();let inflight:Promise<void>|null=null;
 const heartbeat=setInterval(()=>{if(inflight)return;inflight=durableOperation({action:'authHeartbeat',...common,leaseSeconds:60},env).then(()=>{},()=>controller.abort()).finally(()=>{inflight=null;});},10000);
 const context:DispatchContext={signal:controller.signal,begin:async(provider,model)=>{
  if(controller.signal.aborted)throw Error('Execution authorization ended.');
  const committed=[...calls.values()].reduce<number>((total,cost)=>total+(cost??callReservation),0);
  if(callReservation<1||calls.size>=maxCalls||committed+callReservation>policy.maxCostMicrousd)throw Error('Provider call admission exceeds the configured reservation or call limit.');
  const id=randomUUID();calls.set(id,null);
  await durableOperation({action:'authCheckpoint',...common,checkpointId:`${id}:started`,value:{callId:id,provider,model,phase:'started'}},env);
  // Revalidate the grant immediately before returning permission to invoke.
  await durableOperation({action:'authHeartbeat',...common,leaseSeconds:60},env);
  if(controller.signal.aborted)throw Error('Execution authorization ended.');
  return id;
 },record:async(id,evidence)=>{
  if(!calls.has(id))throw Error('Unknown call identity.');
  await durableOperation({action:'authCheckpoint',...common,checkpointId:`${id}:receipt`,value:sanitize({callId:id,...evidence},env)},env);
  const cost=evidence.costMicrousd;calls.set(id,typeof cost==='number'&&Number.isSafeInteger(cost)&&cost>=0?cost:null);
 }};
 const settledCost=()=>{const costs=[...calls.values()];const total=costs.length&&costs.every(c=>c!==null)?costs.reduce<number>((sum,c)=>sum+(c??0),0):null;return Number.isSafeInteger(total)?total:null;};
 let finished=false;
 try{
  const result=await invoke(context);
  if(controller.signal.aborted)throw Error('Execution ended or authorization was revoked; inspect the durable ledger.');
  const cost=settledCost();
  const settled=await durableOperation({action:'authComplete',...common,result:sanitize(result.result,env),actualCostMicrousd:cost},env);finished=true;
  return {...result,result:{...(isRecord(result.result)?result.result:{output:result.result}),execution:{runId,taskId:task.taskId,ledgerStatus:settled.run.status,costBasis:cost===null?'unresolved':'provider_reported_rounded_up',actualCostMicrousd:cost,budgetEnforcement:'admission_reservation_not_provider_spend_cap',maxProviderCalls:maxCalls}}};
 }catch(error){
  if(!finished){try{await durableOperation({action:'authFail',...common,error:'Integration did not complete; inspect checkpoints and reconcile external effects.',actualCostMicrousd:settledCost()},env);}catch{/* Revoked identities cannot settle; expired lease recovery preserves liability. */}}
  throw Error(`${error instanceof Error?String(sanitize(error.message,env)):'Integration failed.'} Durable run: ${runId}`);
 }finally{clearInterval(heartbeat);signal.removeEventListener('abort',abort);if(inflight)await inflight;}
};


/** Execute one immutable stored task. Policy and payload validation precede the exact atomic claim. */
export async function withExistingTaskDispatch(runId:string,taskId:string,env:Env,signal:AbortSignal,
 prepare:(payload:Record<string,unknown>)=>{integrationId:string;operation:string;parameters:Record<string,string|number>;invoke:(context:DispatchContext)=>Promise<DispatchResult>}):Promise<DispatchResult>{
 if(!identifier(runId)||!identifier(taskId))throw Error('Exact run and task IDs are required.');
 if(signal.aborted)throw Error('Cancelled before dispatch.');
 const state=await durableOperation({action:'status',runId},env);
 const task=Array.isArray(state.tasks)?state.tasks.find((value:any)=>value.taskId===taskId):undefined;
 if(!task||task.status!=='pending'||task.executionClass!=='external'||task.maxAttempts!==1||task.attempts!==0||task.requireResourceCapacity!==true||!Number.isSafeInteger(task.reservedCostMicrousd)||task.reservedCostMicrousd<1)throw Error('An unclaimed external task with required resource capacity and one attempt is required.');
 if(!isRecord(task.payload))throw Error('Stored executable task payload is required.');
 const prepared=prepare(task.payload);
 if(!['openrouter','vllm'].includes(prepared.integrationId)||prepared.operation!=='review')throw Error('Planned execution supports bounded OpenRouter or vLLM graph reviews.');
 const policy=dispatchPolicy(prepared.integrationId,prepared.operation,prepared.parameters,env);
 if(task.tool!==`integration:${prepared.integrationId}:${prepared.operation}`||task.resource!==policy.resourceId||task.payload.modelId!==policy.modelId||task.payload.adapterId!==prepared.integrationId||task.payload.operation!==prepared.operation||task.reservedCostMicrousd!==policy.maxCostMicrousd)throw Error('Stored task model, scope or reservation does not match the server policy.');
 if(signal.aborted)throw Error('Cancelled before dispatch.');
 const claimed=await durableOperation({action:'authClaim',runId,taskId,workerId:env.APEX_WORKER_ID,credential:env.APEX_WORKER_CREDENTIAL,leaseSeconds:60},env);
 if(!claimed.task)throw Error('Task is not claimable: dependency, capacity, run state or another worker prevents dispatch.');
 if(claimed.task.taskId!==taskId||JSON.stringify(claimed.task.payload)!==JSON.stringify(task.payload))throw Error('Claimed task differs from the validated stored task; no provider was called.');
 return withClaimedTaskDispatch(claimed.task,runId,{...policy,maxProviderCalls:1},env,signal,prepared.invoke);
}
