import assert from 'node:assert/strict';
import test from 'node:test';
import {access,mkdtemp,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {POST} from '../app/api/control/route';
import {EXECUTION_KINDS,executionLayout,executionView,type ExecutionGraph} from '../lib/execution-graph';

const graph:ExecutionGraph={version:1,runId:'r',nodes:[{id:'task:a',kind:'task',label:'Task A',status:'succeeded'},{id:'task:b',kind:'task',label:'Task B',status:'needs_reconciliation',actualMicrousd:null},{id:'worker:w',kind:'worker',label:'Worker W'}],edges:[{id:'a-b',source:'task:a',target:'task:b',kind:'dependency'},{id:'w-b',source:'worker:w',target:'task:b',kind:'executed'}],summary:{nodeCount:3,edgeCount:2,omittedNodes:0,omittedEdges:0,attemptCoverage:{expected:1,recorded:1,missing:0,complete:true},allCostsResolved:false,knownActualMicrousd:0,unknownCostAttempts:1},limitations:['fixture'],truncated:false};

test('execution view keeps only induced relationships and surfaces selected evidence beyond the cap',()=>{
 const bounded=executionView(graph,'','all','worker:w',false,2);assert.equal(bounded.nodes[0].id,'worker:w');assert.equal(bounded.nodes.length,2);assert.equal(bounded.omitted,1);assert.equal(bounded.edges.length,0);
 const filtered=executionView(graph,'','task',null,false);assert.deepEqual(filtered.edges.map(edge=>edge.id),['a-b']);assert.equal(filtered.nodes[1].actualMicrousd,null);
 const neighborhood=executionView(graph,'','all','task:a',true);assert.equal(neighborhood.nodes.length,2);assert.ok(!neighborhood.nodes.some(node=>node.kind==='worker'));
 assert.equal(executionView(graph,'not present','all',null,false).nodes.length,0);
});

test('specialist contract kind filters, lays out, and retains governed-by edges',()=>{
 const contract:ExecutionGraph={...graph,nodes:[...graph.nodes,{id:'specialist-contract:c1',kind:'specialist_contract',label:'Specialist contract c1',status:'bound',details:{designSha256:'a'.repeat(64)}}],edges:[...graph.edges,{id:'task-contract',source:'task:a',target:'specialist-contract:c1',kind:'governed_by',label:'bound contract; not live authorization'}],summary:{...graph.summary,nodeCount:4,edgeCount:3}};
 assert.ok(EXECUTION_KINDS.includes('specialist_contract'));
 const filtered=executionView(contract,'','specialist_contract',null,false);
 assert.deepEqual(filtered.nodes.map(node=>node.id),['specialist-contract:c1']);
 const layout=executionLayout(filtered.nodes);
 assert.deepEqual(layout.kinds,['specialist_contract']);
 assert.ok(layout.positions.has('specialist-contract:c1'));
 assert.ok(layout.width>=700);
 const neighborhood=executionView(contract,'','all','task:a',true);
 assert.ok(neighborhood.edges.some(edge=>edge.kind==='governed_by'));
});

test('authenticated control graph route reads persisted run evidence and rejects path overrides',async()=>{
 const directory=await mkdtemp(path.join(tmpdir(),'apex-execution-graph-'));
 const previousToken=process.env.INTEGRATION_ACCESS_TOKEN,previousDb=process.env.APEX_CONTROL_DB_PATH;
 process.env.INTEGRATION_ACCESS_TOKEN='graph-fixture-token';process.env.APEX_CONTROL_DB_PATH=path.join(directory,'control.sqlite');
 const send=(body:unknown,token='graph-fixture-token')=>POST(new Request('http://localhost/api/control',{method:'POST',headers:{'Content-Type':'application/json',Authorization:`Bearer ${token}`,Origin:'http://localhost',Host:'localhost'},body:JSON.stringify(body)}));
 try{
  assert.equal((await send({action:'executionGraph',runId:'not-found'},'wrong-token')).status,401);
  assert.equal((await send({action:'executionGraph',runId:'not-found',dbPath:'/arbitrary'})).status,400);
  process.env.APEX_CONTROL_DB_PATH=path.join(directory,'missing-parent','control.sqlite');
  assert.equal((await send({action:'executionGraph',runId:'not-found'})).status,400);
  await assert.rejects(()=>access(path.join(directory,'missing-parent')));
  process.env.APEX_CONTROL_DB_PATH=path.join(directory,'control.sqlite');
  const created=await send({action:'createFixture',agents:30,idempotencyKey:'execution-graph-fixture'});assert.equal(created.status,200);const runId=(await created.json()).state.run.id;
  const advanced=await send({action:'advanceFixture',runId});assert.equal(advanced.status,200);
  const response=await send({action:'executionGraph',runId});assert.equal(response.status,200);const result=(await response.json()).state as ExecutionGraph;
  assert.equal(result.runId,runId);assert.ok(result.nodes.some(node=>node.kind==='attempt'));assert.ok(result.edges.some(edge=>edge.kind==='dependency'));assert.ok(result.edges.every(edge=>result.nodes.some(node=>node.id===edge.source)&&result.nodes.some(node=>node.id===edge.target)));
  assert.ok(!JSON.stringify(result).includes('leaseToken'));assert.equal(result.summary.unknownCostAttempts,0);
 }finally{if(previousToken===undefined)delete process.env.INTEGRATION_ACCESS_TOKEN;else process.env.INTEGRATION_ACCESS_TOKEN=previousToken;if(previousDb===undefined)delete process.env.APEX_CONTROL_DB_PATH;else process.env.APEX_CONTROL_DB_PATH=previousDb;await rm(directory,{recursive:true,force:true});}
});
