import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {ExecutionRequestConflictError,ExecutionRequestRecoveryError,resetExecutionRequestClientForTests,startIdempotentIntegrationRequest} from '../lib/execution-request-client';
import {IntegrationRuntime} from '../lib/integration-runtime';
import type {Snapshot} from '../lib/graph';

function graph():Snapshot{return {version:1,name:'Request fixture',nodes:[{id:'n1',name:'one',kind:'file',path:'src/one.ts',summary:'',confidence:'parsed'}],edges:[],warnings:[],truncated:false};}
const env={OPENROUTER_API_KEY:'fixture-secret',OPENROUTER_MODEL:'test/model'};
const payload={integrationId:'openrouter',operation:'review',input:{goal:'Fixture request',graph:graph(),parameters:{}}};
const waitFor=async(fn:()=>boolean)=>{for(let i=0;i<150;i++){if(fn())return;await new Promise(resolve=>setTimeout(resolve,5));}throw new Error('Job did not settle.');};
function jobOf(outcome:{job:{id:string}|null}){if(!outcome.job)throw new Error('Expected a live in-memory job.');return outcome.job;}

test('web start uses the durable job UUID, replays within process, and conflicts on changed payload',async()=>{
 resetExecutionRequestClientForTests();
 const directory=mkdtempSync(path.join(tmpdir(),'apex-request-client-')),dbPath=path.join(directory,'control.sqlite');let calls=0;
 const runtime=new IntegrationRuntime({env,execute:async()=>{calls++;return {result:{ok:true}};}});
 const request=()=>startIdempotentIntegrationRequest({idempotencyKey:'fixture-key-01',scopeToken:'workspace-secret-token',payload,env:{...env,APEX_CONTROL_DB_PATH:dbPath},findJob:id=>runtime.get(id),startJob:(value,id)=>runtime.startRegistered(value,id)});
 try{
  const first=await request(),firstJob=jobOf(first);assert.equal(first.replayed,false);assert.match(firstJob.id,/^[0-9a-f-]{36}$/);
  await waitFor(()=>runtime.get(firstJob.id)?.status==='succeeded');
  const replay=await request(),replayJob=jobOf(replay);assert.equal(replay.replayed,true);assert.equal(replayJob.id,firstJob.id);assert.equal(calls,1);
  await assert.rejects(startIdempotentIntegrationRequest({idempotencyKey:'fixture-key-01',scopeToken:'workspace-secret-token',payload:{...payload,input:{...payload.input,goal:'changed'}},env:{...env,APEX_CONTROL_DB_PATH:dbPath},findJob:id=>runtime.get(id),startJob:(value,id)=>runtime.startRegistered(value,id)}),ExecutionRequestConflictError);
 }finally{rmSync(directory,{recursive:true,force:true});resetExecutionRequestClientForTests();}
});

test('request from a restarted process returns recovery-required and does not dispatch again',async()=>{
 resetExecutionRequestClientForTests();
 const directory=mkdtempSync(path.join(tmpdir(),'apex-request-restart-')),dbPath=path.join(directory,'control.sqlite');let dispatches=0;
 const first=await startIdempotentIntegrationRequest({idempotencyKey:'restart-key-01',scopeToken:'workspace-secret-token',payload,env:{...env,APEX_CONTROL_DB_PATH:dbPath},findJob:()=>null,startJob:(_value,id)=>{dispatches++;return {id};}}),firstJob=jobOf(first);
 assert.equal(firstJob.id.length,36);assert.equal(dispatches,1);
 // A fresh client cache models a server restart: registry is durable, runtime is not.
 resetExecutionRequestClientForTests();
 await assert.rejects(startIdempotentIntegrationRequest({idempotencyKey:'restart-key-01',scopeToken:'workspace-secret-token',payload,env:{...env,APEX_CONTROL_DB_PATH:dbPath},findJob:()=>null,startJob:(_value,id)=>{dispatches++;return {id};}}),error=>{
  assert.ok(error instanceof ExecutionRequestRecoveryError);assert.equal(error.jobId,firstJob.id);return true;
 });
 assert.equal(dispatches,1);
 resetExecutionRequestClientForTests();rmSync(directory,{recursive:true,force:true});
});

test('concurrent web callers share one pending registration and one dispatch',async()=>{
 resetExecutionRequestClientForTests();
 const directory=mkdtempSync(path.join(tmpdir(),'apex-request-concurrent-')),dbPath=path.join(directory,'control.sqlite');let dispatches=0,release:(()=>void)|undefined;
 const runtime=new IntegrationRuntime({env,execute:async()=>{dispatches++;await new Promise<void>(resolve=>{release=resolve;});return {result:{ok:true}};}});
 const request=()=>startIdempotentIntegrationRequest({idempotencyKey:'concurrent-key-01',scopeToken:'workspace-secret-token',payload,env:{...env,APEX_CONTROL_DB_PATH:dbPath},findJob:id=>runtime.get(id),startJob:(value,id)=>runtime.startRegistered(value,id)});
 try{const [one,two]=await Promise.all([request(),request()]),oneJob=jobOf(one),twoJob=jobOf(two);assert.equal(oneJob.id,twoJob.id);await waitFor(()=>dispatches===1);release?.();await waitFor(()=>runtime.get(oneJob.id)?.status==='succeeded');assert.equal(dispatches,1);}finally{release?.();resetExecutionRequestClientForTests();rmSync(directory,{recursive:true,force:true});}
});
