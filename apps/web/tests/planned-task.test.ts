import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import test from 'node:test';
import {mkdtemp,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {durableOperation} from '../lib/durable-dispatch';
import {executePlannedTask} from '../lib/integration-runtime';
import {POST as postPlannedTask} from '../app/api/planned-tasks/route';
import type {Snapshot} from '../lib/graph';

const root=path.resolve(process.cwd(),'../..');
const graph:Snapshot={version:1,name:'Compiled plan fixture',nodes:[{id:'node-one',name:'One',kind:'file',path:'one.py',summary:'fixture evidence',confidence:'parsed'}],edges:[],warnings:[],truncated:false};
const model='review-model',modelId='test/model',resourceId='model:test/model',toolId='integration:openrouter:review',reservation=1000;

type Fixture={directory:string;env:Record<string,string>;runId:string;taskId:string;plan:Record<string,any>};
async function fixture(options:{twoTasks?:boolean;transform?:(plan:Record<string,any>)=>void}={}):Promise<Fixture>{
 const directory=await mkdtemp(path.join(tmpdir(),'apex-planned-task-'));
 const env:Record<string,string>={APEX_CONTROL_DB_PATH:path.join(directory,'control.sqlite'),APEX_WORKER_ID:'planned-fixture-worker',OPENROUTER_API_KEY:'fixture-provider-secret',OPENROUTER_MODEL:modelId,APEX_INTEGRATION_POLICIES_JSON:JSON.stringify([{integrationId:'openrouter',operation:'review',resourceId,modelId:modelId,maxCostMicrousd:reservation}])};
 try{
  const enrolled=await durableOperation({action:'enrollWorker',workerId:env.APEX_WORKER_ID,principalId:'planned-fixture-principal',expiresAt:Date.now()/1000+120},env);
  env.APEX_WORKER_CREDENTIAL=enrolled.credential;
  await durableOperation({action:'grantAccess',principalId:'planned-fixture-principal',tool:toolId,resource:resourceId,maxBudgetMicrousd:5000,expiresAt:Date.now()/1000+120},env);
  await durableOperation({action:'configureResourceCapacity',resourceId,maxConcurrency:1},env);
  await durableOperation({action:'configureResourceCapacity',resourceId:'model:other',maxConcurrency:1},env);
  const sourceTask={id:'source-review',duration_estimate:1,options:[{model,estimated_cost_microusd:reservation,duration_estimate:1}]};
  const taskInputs:Record<string,unknown>={'source-review':{goal:'Inspect only this supplied graph.',graph,parameters:{maxOutputTokens:100}}};
  const problem={tasks:[sourceTask],budget_microusd:reservation,capacities:{[model]:1}};
  const modelBindings={[model]:{configured:true,adapterId:'openrouter',operation:'review',modelId,resourceId,toolId,costMicrousd:reservation,maxParallel:1}};
  const raw=execFileSync('python3',['-m','apexgraphswarm.lab'],{cwd:root,encoding:'utf8',input:JSON.stringify({action:'compileDelegation',problem,modelBindings,taskInputs}),env:{...process.env,PYTHONDONTWRITEBYTECODE:'1'}});
  const compiled=JSON.parse(raw) as {plan:Record<string,any>;budgetMicrousd:number};
  assert.equal(compiled.plan.tasks.length,1);
  let plan=structuredClone(compiled.plan);
  if(options.twoTasks){const first=plan.tasks[0];plan.tasks.push({...structuredClone(first),id:'dependent-sibling',dependencies:[first.id],reservedCostMicrousd:0,payload:{...first.payload,sourceTaskId:'sibling'}});}
  options.transform?.(plan);
  const created=await durableOperation({action:'create',idempotencyKey:`compiled-${Date.now()}-${Math.random()}`,budgetMicrousd:compiled.budgetMicrousd,plan},env);
  const task=created.tasks.find((item:any)=>item.id==='task-'+createHash('sha256').update('source-review').digest('hex'))??created.tasks[0];
  assert.ok(task?.taskId);
  return {directory,env,runId:created.run.id,taskId:task.taskId,plan};
 }catch(error){await rm(directory,{recursive:true,force:true});throw error;}
}
function providerResponse(id='generation-planned-fixture',cost='0.0000004'){return new Response(JSON.stringify({id,model:modelId,usage:{prompt_tokens:9,completion_tokens:4,total_tokens:13,cost},choices:[{message:{content:JSON.stringify({summary:'Grounded fixture result',findings:[]})}}]}),{headers:{'content-type':'application/json'}});}
async function runCount(dbPath:string){const output=execFileSync('python3',['-c','import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); print(c.execute("select count(*) from runs").fetchone()[0]); c.close()',dbPath],{encoding:'utf8'});return Number(output.trim());}

test('Python-compiled execution contract dispatches the exact task and creates no second run',async()=>{
 const state=await fixture(),originalFetch=globalThis.fetch;let calls=0;
 try{
  globalThis.fetch=async(url,init)=>{calls++;assert.equal(String(url),'https://openrouter.ai/api/v1/chat/completions');const body=JSON.parse(String(init?.body));assert.equal(body.model,modelId);assert.equal(body.max_tokens,100);assert.match(body.messages[1].content,/Inspect only this supplied graph/);assert.match(body.messages[1].content,/node-one/);return providerResponse();};
  const result=await executePlannedTask(state.runId,state.taskId,state.env);
  assert.equal(calls,1);
  assert.equal((result.result as any).execution.runId,state.runId);
  assert.equal((result.result as any).execution.taskId,state.taskId);
  assert.equal((result.result as any).execution.actualCostMicrousd,1);
  assert.equal(await runCount(state.env.APEX_CONTROL_DB_PATH),1);
  const saved=await durableOperation({action:'status',runId:state.runId},state.env);
  assert.equal(saved.run.status,'succeeded');
  assert.equal(saved.tasks.find((item:any)=>item.taskId===state.taskId).status,'succeeded');
 }finally{globalThis.fetch=originalFetch;await rm(state.directory,{recursive:true,force:true});}
});

test('exact task dispatch leaves a dependent sibling pending',async()=>{
 const state=await fixture({twoTasks:true}),originalFetch=globalThis.fetch;let calls=0;
 try{
  globalThis.fetch=async()=>{calls++;return providerResponse('generation-exact-task','0.000001');};
  const result=await executePlannedTask(state.runId,state.taskId,state.env);
  assert.equal((result.result as any).execution.taskId,state.taskId);
  assert.equal(calls,1);
  const saved=await durableOperation({action:'status',runId:state.runId},state.env);
  const completed=saved.tasks.find((item:any)=>item.taskId===state.taskId);
  const sibling=saved.tasks.find((item:any)=>item.id==='dependent-sibling');
  assert.equal(completed.status,'succeeded');
  assert.equal(sibling.status,'pending');
  assert.deepEqual(sibling.dependencies,[completed.id]);
  assert.equal(await runCount(state.env.APEX_CONTROL_DB_PATH),1);
 }finally{globalThis.fetch=originalFetch;await rm(state.directory,{recursive:true,force:true});}
});

test('model, resource, and reservation mismatches are rejected before provider invocation',async(t)=>{
 const cases:[string,(plan:Record<string,any>)=>void][]=[
  ['model',plan=>{plan.tasks[0].payload.modelId='unconfigured/other';}],
  ['resource',plan=>{plan.tasks[0].resource='model:other';}],
  ['reservation',plan=>{plan.tasks[0].reservedCostMicrousd=reservation-1;}],
 ];
 for(const [label,transform] of cases){await t.test(label,async()=>{
  const state=await fixture({transform}),originalFetch=globalThis.fetch;let calls=0;
  try{globalThis.fetch=async()=>{calls++;return providerResponse();};await assert.rejects(()=>executePlannedTask(state.runId,state.taskId,state.env));assert.equal(calls,0);
   const saved=await durableOperation({action:'status',runId:state.runId},state.env);assert.equal(saved.tasks[0].status,'pending');assert.equal(saved.tasks[0].attempts,0);
  }finally{globalThis.fetch=originalFetch;await rm(state.directory,{recursive:true,force:true});}
 });}
});

test('parallel duplicate dispatch has one winner and one provider invocation',async()=>{
 const state=await fixture(),originalFetch=globalThis.fetch;let calls=0,release!:()=>void,entered!:()=>void;
 const enteredFetch=new Promise<void>(resolve=>{entered=resolve;});const gate=new Promise<void>(resolve=>{release=resolve;});
 try{
  globalThis.fetch=async()=>{calls++;entered();await gate;return providerResponse('generation-race','0.000001');};
  const first=executePlannedTask(state.runId,state.taskId,state.env);
  await enteredFetch;
  await assert.rejects(()=>executePlannedTask(state.runId,state.taskId,state.env),/unclaimed|claimable|pending|claim/i);
  release();const result=await first;
  assert.equal(calls,1);assert.equal((result.result as any).execution.runId,state.runId);
  const saved=await durableOperation({action:'status',runId:state.runId},state.env);assert.equal(saved.tasks[0].attempts,1);assert.equal(saved.tasks[0].status,'succeeded');
  assert.equal(await runCount(state.env.APEX_CONTROL_DB_PATH),1);
 }finally{release?.();globalThis.fetch=originalFetch;await rm(state.directory,{recursive:true,force:true});}
});

test('abort after provider invocation preserves unresolved reservation for reconciliation',async()=>{
 const state=await fixture(),originalFetch=globalThis.fetch,controller=new AbortController();let entered!:()=>void;
 const enteredFetch=new Promise<void>(resolve=>{entered=resolve;});
 try{
  globalThis.fetch=async(_url,init)=>new Promise<Response>((_resolve,reject)=>{entered();const signal=init?.signal as AbortSignal;signal.addEventListener('abort',()=>reject(new DOMException('aborted','AbortError')),{once:true});});
  const execution=executePlannedTask(state.runId,state.taskId,state.env,controller.signal);
  await enteredFetch;controller.abort();await assert.rejects(()=>execution);
  const saved=await durableOperation({action:'status',runId:state.runId},state.env);
  assert.equal(saved.tasks[0].status,'needs_reconciliation');assert.equal(saved.tasks[0].result,null);
  assert.equal(saved.run.reservedMicrousd,reservation);assert.equal(saved.run.spentMicrousd,0);
  assert.equal(await runCount(state.env.APEX_CONTROL_DB_PATH),1);
 }finally{globalThis.fetch=originalFetch;await rm(state.directory,{recursive:true,force:true});}
});

test('planned-task route requires workspace auth and rejects browser-supplied execution inputs',async()=>{
 const previous=process.env.INTEGRATION_ACCESS_TOKEN;
 process.env.INTEGRATION_ACCESS_TOKEN='planned-route-fixture-token';
 const request=(body:unknown,authorization?:string,origin?:string)=>new Request('http://127.0.0.1:3010/api/planned-tasks',{method:'POST',headers:{'content-type':'application/json','host':'127.0.0.1:3010',...(authorization?{authorization}:{}),...(origin?{origin}:{})},body:JSON.stringify(body)});
 try{
  const unauthorized=await postPlannedTask(request({runId:'run-fixture',taskId:'task-fixture'}));
  assert.equal(unauthorized.status,401);
  const wrongOrigin=await postPlannedTask(request({runId:'run-fixture',taskId:'task-fixture'},'Bearer planned-route-fixture-token','https://untrusted.example'));
  assert.equal(wrongOrigin.status,401);
  const override=await postPlannedTask(request({runId:'run-fixture',taskId:'task-fixture',goal:'replace stored goal'},'Bearer planned-route-fixture-token'));
  assert.equal(override.status,400);
  assert.match((await override.json()).error,/Only exact runId and taskId/);
 }finally{if(previous===undefined)delete process.env.INTEGRATION_ACCESS_TOKEN;else process.env.INTEGRATION_ACCESS_TOKEN=previous;}
});

test('authenticated planned-task route executes the persisted exact task using only mocked provider transport',async()=>{
 const state=await fixture(),originalFetch=globalThis.fetch,token='planned-route-execution-fixture-token';
 const names=['INTEGRATION_ACCESS_TOKEN','APEX_CONTROL_DB_PATH','APEX_WORKER_ID','APEX_WORKER_CREDENTIAL','OPENROUTER_API_KEY','OPENROUTER_MODEL','APEX_INTEGRATION_POLICIES_JSON'] as const;
 const previous=Object.fromEntries(names.map(name=>[name,process.env[name]]));let calls=0;
 try{
  Object.assign(process.env,{INTEGRATION_ACCESS_TOKEN:token,...state.env});
  globalThis.fetch=async()=>{calls++;return providerResponse('generation-route-fixture','0.000002');};
  const response=await postPlannedTask(new Request('http://127.0.0.1:3010/api/planned-tasks',{method:'POST',headers:{'content-type':'application/json','authorization':`Bearer ${token}`,origin:'http://127.0.0.1:3010',host:'127.0.0.1:3010'},body:JSON.stringify({runId:state.runId,taskId:state.taskId})}));
  assert.equal(response.status,200,JSON.stringify(await response.clone().json()));
  const body=await response.json();assert.equal(body.result.result.execution.runId,state.runId);assert.equal(body.result.result.execution.taskId,state.taskId);assert.equal(calls,1);assert.equal(await runCount(state.env.APEX_CONTROL_DB_PATH),1);
 }finally{
  globalThis.fetch=originalFetch;
  for(const name of names){const value=previous[name];if(value===undefined)delete process.env[name];else process.env[name]=value;}
  await rm(state.directory,{recursive:true,force:true});
 }
});
