import assert from 'node:assert/strict';
import test from 'node:test';
import {mkdtemp,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {dispatchPolicy,durableOperation,withDurableDispatch} from '../lib/durable-dispatch';
import {IntegrationRuntime} from '../lib/integration-runtime';
import type {Snapshot} from '../lib/graph';

const graph:Snapshot={version:1,name:'Receipt fixture',nodes:[{id:'n1',name:'One',kind:'file',path:'one.py',summary:'',confidence:'parsed'}],edges:[],warnings:[],truncated:false};
async function workspace(operation='review'){
 const directory=await mkdtemp(path.join(tmpdir(),'apex-durable-'));
 const env:Record<string,string>={APEX_CONTROL_DB_PATH:path.join(directory,'control.sqlite'),APEX_WORKER_ID:'fixture-worker',OPENROUTER_API_KEY:'fixture-provider-secret',OPENROUTER_MODEL:'test/model',APEX_INTEGRATION_POLICIES_JSON:JSON.stringify([{integrationId:'openrouter',operation,resourceId:'model:test/model',modelId:'test/model',maxCostMicrousd:1000}])};
 const enrolled=await durableOperation({action:'enrollWorker',workerId:'fixture-worker',principalId:'fixture-principal',expiresAt:Date.now()/1000+120},env);
 env.APEX_WORKER_CREDENTIAL=enrolled.credential;
 const grant=await durableOperation({action:'grantAccess',principalId:'fixture-principal',tool:`integration:openrouter:${operation}`,resource:'model:test/model',maxBudgetMicrousd:5000,expiresAt:Date.now()/1000+120},env);
 return {directory,env,grant};
}
async function settled(runtime:IntegrationRuntime,id:string){for(let i=0;i<200;i++){const state=runtime.get(id)!;if(['succeeded','failed','cancelled'].includes(state.status))return state;await new Promise(resolve=>setTimeout(resolve,10));}throw Error('Fixture did not settle');}

test('policy pins scope, model and harness parameters before invocation',async()=>{
 assert.throws(()=>dispatchPolicy('openrouter','review',{},{}),/enrolled/);
 const env={APEX_WORKER_ID:'w',APEX_WORKER_CREDENTIAL:'fixture',OPENROUTER_MODEL:'model',APEX_INTEGRATION_POLICIES_JSON:JSON.stringify([{integrationId:'openrouter',operation:'review',resourceId:'resource',maxCostMicrousd:5,modelId:'different'}])};
 assert.throws(()=>dispatchPolicy('openrouter','review',{},env),/pin/);
 let invoked=false;
 await assert.rejects(()=>withDurableDispatch('openrouter','review',{},env,new AbortController().signal,'job',async()=>{invoked=true;return {result:{}};}));
 assert.equal(invoked,false);
});

test('actual adapter persists a pre-call checkpoint and normalized receipt in durable accounting',async()=>{
 const {directory,env}=await workspace(),originalFetch=globalThis.fetch;let calls=0;
 try{
  globalThis.fetch=async(url)=>{
   assert.equal(String(url),'https://openrouter.ai/api/v1/chat/completions');calls++;
   const ledger=await durableOperation({action:'ledger'},env);assert.equal(ledger.totalAttempts,1);
   const checkpoints=await durableOperation({action:'checkpoints',taskId:ledger.attempts[0].taskId},env);
   assert.ok(JSON.stringify(checkpoints).includes('started'));
   return new Response(JSON.stringify({id:'gen-receipt-fixture',model:'test/model',usage:{prompt_tokens:5,completion_tokens:2,total_tokens:7,cost:'0.0000004'},choices:[{message:{content:JSON.stringify({summary:'grounded',findings:[]})}}]}));
  };
  const runtime=new IntegrationRuntime({env});const job=runtime.start({integrationId:'openrouter',operation:'review',input:{goal:'Fixture',graph,parameters:{}}});
  const state=await settled(runtime,job.id);assert.equal(state.status,'succeeded',state.error||'Expected success');assert.equal(calls,1);
  const execution=(state.result as any).execution;assert.equal(execution.actualCostMicrousd,1);assert.equal(execution.ledgerStatus,'succeeded');
  const saved=await durableOperation({action:'status',runId:execution.runId},env);assert.equal(saved.run.spentMicrousd,1);
  const receipt=await durableOperation({action:'checkpoints',taskId:execution.taskId},env);assert.ok(JSON.stringify(receipt).includes('gen-receipt-fixture'));assert.ok(!JSON.stringify(saved).includes(env.APEX_WORKER_CREDENTIAL));
 }finally{globalThis.fetch=originalFetch;await rm(directory,{recursive:true,force:true});}
});

test('unknown provider cost preserves output and reservation for reconciliation',async()=>{
 const {directory,env}=await workspace(),originalFetch=globalThis.fetch;
 try{
  globalThis.fetch=async()=>new Response(JSON.stringify({id:'gen-unknown',model:'test/model',usage:{prompt_tokens:5,completion_tokens:2,total_tokens:7},choices:[{message:{content:JSON.stringify({summary:'output retained',findings:[]})}}]}));
  const runtime=new IntegrationRuntime({env});const job=runtime.start({integrationId:'openrouter',operation:'review',input:{goal:'Fixture',graph,parameters:{}}});
  const state=await settled(runtime,job.id);assert.equal(state.status,'succeeded',state.error||'Expected success');
  const execution=(state.result as any).execution;assert.equal(execution.actualCostMicrousd,null);assert.equal(execution.ledgerStatus,'needs_reconciliation');
  const saved=await durableOperation({action:'status',runId:execution.runId},env);assert.equal(saved.run.reservedMicrousd,1000);assert.equal(saved.ledger.allCostsResolved,false);assert.ok(JSON.stringify(saved).includes('output retained'));
 }finally{globalThis.fetch=originalFetch;await rm(directory,{recursive:true,force:true});}
});

test('failed parallel model calls preserve the completed sibling receipt without dispatching a critic',async()=>{
 const {directory,env}=await workspace('delegate'),originalFetch=globalThis.fetch;let calls=0;
 try{
  globalThis.fetch=async()=>{calls++;if(calls===1)return new Response(JSON.stringify({id:'gen-sibling',model:'test/model',usage:{prompt_tokens:5,completion_tokens:2,total_tokens:7,cost:'0.000010'},choices:[{message:{content:JSON.stringify({summary:'sibling result',findings:[]})}}]}));return new Response('{}',{status:503});};
  const runtime=new IntegrationRuntime({env});const job=runtime.start({integrationId:'openrouter',operation:'delegate',input:{goal:'Fixture',graph,parameters:{}}});const state=await settled(runtime,job.id);assert.equal(state.status,'failed');assert.equal(calls,2);
  const ledger=await durableOperation({action:'ledger'},env);assert.equal(ledger.unresolvedCostCount,1);
  const checkpoints=await durableOperation({action:'checkpoints',taskId:ledger.attempts[0].taskId},env);assert.ok(JSON.stringify(checkpoints).includes('gen-sibling'));
 }finally{globalThis.fetch=originalFetch;await rm(directory,{recursive:true,force:true});}
});


test('zero reservation cannot invoke a provider',async()=>{
 const {directory,env}=await workspace();
 try{const policies=JSON.parse(env.APEX_INTEGRATION_POLICIES_JSON);policies[0].maxCostMicrousd=0;env.APEX_INTEGRATION_POLICIES_JSON=JSON.stringify(policies);let invoked=false;
 await assert.rejects(()=>withDurableDispatch('openrouter','review',{},env,new AbortController().signal,'zero-reservation',async context=>{await context.begin('openrouter','test/model');invoked=true;return {result:{}};}),/admission/);assert.equal(invoked,false);
 }finally{await rm(directory,{recursive:true,force:true});}
});

test('call limit prevents an extra provider invocation',async()=>{
 const {directory,env}=await workspace();
 try{let calls=0;await assert.rejects(()=>withDurableDispatch('openrouter','review',{},env,new AbortController().signal,'call-limit',async context=>{const id=await context.begin('openrouter','test/model');calls++;await context.record(id,{costMicrousd:1});await context.begin('openrouter','test/model');calls++;return {result:{}};}),/admission/);assert.equal(calls,1);
 }finally{await rm(directory,{recursive:true,force:true});}
});


test('grant revoked after claim prevents the provider invocation',async()=>{
 const {directory,env,grant}=await workspace();
 try{let invoked=false;await assert.rejects(()=>withDurableDispatch('openrouter','review',{},env,new AbortController().signal,'revocation-boundary',async context=>{await durableOperation({action:'revokeAccess',grantId:grant.grantId},env);await context.begin('openrouter','test/model');invoked=true;return {result:{}};}));assert.equal(invoked,false);
 }finally{await rm(directory,{recursive:true,force:true});}
});
