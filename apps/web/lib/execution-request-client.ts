import {createHash,randomUUID} from 'node:crypto';
import {execFile} from 'node:child_process';
import path from 'node:path';
import {mkdir} from 'node:fs/promises';

type PublicJob={id:string};
type RegistryResponse={created:boolean;jobId:string};
type LocalEntry={payloadDigest:string;jobId:string};
const MAX_LOCAL_ENTRIES=1000;
const known=new Map<string,LocalEntry>();
const pending=new Map<string,{payloadDigest:string;promise:Promise<PublicJob>}>();

export class ExecutionRequestConflictError extends Error{
 constructor(){super('Idempotency-Key was already used for a different integration request.');this.name='ExecutionRequestConflictError';}
}
export class ExecutionRequestRecoveryError extends Error{
 constructor(readonly jobId:string,readonly runId:string|null=null){super('This request was already registered, but its in-memory execution is unavailable. Recovery is required; automatic redispatch was refused.');this.name='ExecutionRequestRecoveryError';}
}

function sha256(value:string){return createHash('sha256').update(value).digest('hex');}
function canonical(value:unknown):string{
 if(value===null||typeof value==='string'||typeof value==='boolean')return JSON.stringify(value);
 if(typeof value==='number'){if(!Number.isFinite(value))throw new Error('Request body must contain finite JSON numbers.');return JSON.stringify(value);}
 if(Array.isArray(value))return `[${value.map(canonical).join(',')}]`;
 if(value&&typeof value==='object'){
  const record=value as Record<string,unknown>;
  return `{${Object.keys(record).sort().map(key=>`${JSON.stringify(key)}:${canonical(record[key])}`).join(',')}}`;
 }
 throw new Error('Request body must be canonical JSON data.');
}
function dbConfiguration(env:Record<string,string|undefined>){
 const root=path.resolve(process.cwd(),'../..');
 const dbPath=env.APEX_CONTROL_DB_PATH?path.resolve(env.APEX_CONTROL_DB_PATH):path.join(root,'.runtime','control.sqlite');
 return {root,dbPath};
}
async function registryCommand<T>(dbPath:string,root:string,input:Record<string,unknown>):Promise<T>{
 await mkdir(path.dirname(dbPath),{recursive:true,mode:0o700});
 return new Promise((resolve,reject)=>{
  execFile('python3',['-m','apexgraphswarm.request_registry'],{cwd:root,timeout:20_000,maxBuffer:64*1024,encoding:'utf8',env:{NODE_ENV:process.env.NODE_ENV,PATH:process.env.PATH,LANG:'C.UTF-8',PYTHONDONTWRITEBYTECODE:'1'}},(error,stdout)=>{
   try{
    const response=JSON.parse(stdout) as {data?:T;error?:string};
    if(response.error?.startsWith('Idempotency-Key was already used for a different integration request.'))reject(new ExecutionRequestConflictError());
    else if(error||response.error||!response.data)reject(new Error(response.error||'Local request registry failed.'));
    else resolve(response.data);
   }catch{reject(new Error('Local request registry returned an invalid response.'));}
  }).stdin?.end(JSON.stringify({...input,dbPath}));
 });
}
async function register(dbPath:string,root:string,requestKeyHash:string,scopeHash:string,payloadDigest:string):Promise<RegistryResponse>{
 const response=await registryCommand<RegistryResponse>(dbPath,root,{action:'register',requestKeyHash,scopeHash,payloadDigest,candidateJobId:randomUUID()});
 if(typeof response.created!=='boolean'||typeof response.jobId!=='string')throw new Error('Local request registry returned an invalid registration.');
 return response;
}
async function lookupRunId(dbPath:string,root:string,jobId:string):Promise<string|null>{
 const response=await registryCommand<{runId:string|null}>(dbPath,root,{action:'lookupRun',jobId});
 if(response.runId!==null&&typeof response.runId!=='string')throw new Error('Local run lookup returned an invalid response.');
 return response.runId;
}

export async function startIdempotentIntegrationRequest(options:{
 idempotencyKey:string;scopeToken:string;payload:unknown;env:Record<string,string|undefined>;
 findJob:(jobId:string)=>PublicJob|null;startJob:(payload:unknown,jobId:string)=>PublicJob;
}):Promise<{job:PublicJob;replayed:boolean;recoveryRequired?:false}|{job:null;replayed:true;recoveryRequired:true;jobId:string;runId:string|null;durableRunIdempotencyKey:string}>{
 const {idempotencyKey,scopeToken,payload,env}=options;
 if(typeof idempotencyKey!=='string'||idempotencyKey.length<1||idempotencyKey.length>200||!/^[\x21-\x7e]+$/.test(idempotencyKey))throw new Error('Idempotency-Key must contain 1 to 200 visible ASCII characters.');
 if(typeof scopeToken!=='string'||scopeToken.length<1)throw new Error('Authenticated request scope is missing.');
 const {root,dbPath}=dbConfiguration(env);
 const requestKeyHash=sha256(`apex-request-key\0${idempotencyKey}`),scopeHash=sha256(`apex-request-scope\0${scopeToken}`),payloadDigest=sha256(canonical(payload));
 const localKey=`${scopeHash}:${requestKeyHash}`;
 const priorPending=pending.get(localKey);
 if(priorPending){if(priorPending.payloadDigest!==payloadDigest)throw new ExecutionRequestConflictError();return {job:await priorPending.promise,replayed:true};}
 const prior=known.get(localKey);
 if(prior){if(prior.payloadDigest!==payloadDigest)throw new ExecutionRequestConflictError();const existing=options.findJob(prior.jobId);if(existing)return {job:existing,replayed:true};const runId=await lookupRunId(dbPath,root,prior.jobId);return {job:null,replayed:true,recoveryRequired:true,jobId:prior.jobId,runId,durableRunIdempotencyKey:`integration-${prior.jobId}`};}
 const operation=(async()=>{
  const registration=await register(dbPath,root,requestKeyHash,scopeHash,payloadDigest);
  const entry={payloadDigest,jobId:registration.jobId};known.set(localKey,entry);
  while(known.size>MAX_LOCAL_ENTRIES)known.delete(known.keys().next().value!);
  if(registration.created){
   // The durable registry row precedes queue admission. Any failure after this
   // point is treated as uncertain and future retries are fail-closed.
   return options.startJob(payload,registration.jobId);
  }
  const existing=options.findJob(registration.jobId);
  if(existing)return existing;
  const runId=await lookupRunId(dbPath,root,registration.jobId);
  throw new ExecutionRequestRecoveryError(registration.jobId,runId);
 })();
 pending.set(localKey,{payloadDigest,promise:operation});
 try{return {job:await operation,replayed:false};}
 finally{pending.delete(localKey);}
}

export function resetExecutionRequestClientForTests(){known.clear();pending.clear();}
