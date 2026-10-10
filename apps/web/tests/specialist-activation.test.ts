import test from 'node:test';
import assert from 'node:assert/strict';
import {createStarterDesign} from '../lib/specialist-design';
import {executableReviewTasks,specialistActivationRequest} from '../lib/specialist-activation';
function fixture(){
 const design=createStarterDesign(),agent=design.agents[0],node=design.nodes[0];
 agent.harnessId='openrouter';agent.modelRef='fixture/model';agent.policy.subjectRef='principal:fixture';agent.policy.actions=['read'];agent.policy.resourceIds=[node.id];agent.policy.audience='apexgraphswarm';agent.policy.purpose='review';agent.policy.approvalQuorum=2;
 agent.tools=[{serverId:'declared-provider',toolName:'review',gatewayId:'local'}];
 const task={id:'task',agentId:'logical-reviewer',executionClass:'external',requireResourceCapacity:true,tool:'integration:openrouter:review',resource:'model:fixture/model',payload:{sourceTaskId:'review',modelId:'fixture/model',adapterId:'openrouter',operation:'review',execution:{version:1,integrationId:'openrouter',operation:'review',input:{goal:'Review this exact fixture.',graph:{version:1,name:'fixture',nodes:[{id:'n1',name:'One',kind:'file',path:'one.py',summary:'',confidence:'parsed'}],edges:[],warnings:[],truncated:false},parameters:{maxOutputTokens:600}}}}};
 return {design,agent,node,task,selection:{specialistId:agent.id,nodeId:node.id,action:'read',workerId:'worker:fixture',mcpBinding:agent.tools[0],idempotencyKey:'fixture-request'}};
}
test('handoff preserves exact compiled input but cannot supply approvals or mint credentials',()=>{
 const {design,agent,node,task,selection}=fixture();
 const tasks=executableReviewTasks({result:{plan:{version:1,agents:[{id:task.agentId}],tasks:[task]}}});
 const result=specialistActivationRequest(design,tasks[0],selection,100);
 assert.equal(result.action,'createSpecialistContract');assert.equal(result.assignment.logicalAgentId,task.agentId);assert.equal(result.assignment.specialistId,agent.id);assert.equal(result.assignment.nodeId,node.id);assert.equal(result.assignment.principalId,agent.policy.subjectRef);assert.deepEqual(result.assignment.executionInput,task.payload.execution.input);assert.equal(result.assignment.expiresAt,100+agent.policy.ttlSeconds);
 assert.equal('approverIds' in result.assignment,false);assert.equal('credential' in result,false);assert.equal(result.design.agents[0].policy.approvalQuorum,2);
});
test('unassigned scope and unlisted tool cannot be exported as a valid activation request',()=>{
 const {design,task,selection}=fixture();
 assert.throws(()=>specialistActivationRequest(design,task,{...selection,mcpBinding:{...selection.mcpBinding,toolName:'other'}},100),/tool declaration/);
 design.nodes[0].teamIds=[];
 assert.throws(()=>specialistActivationRequest(design,task,selection,100),/assigned/);
});
test('model substitution, privileged action, compile-only and duplicate task IDs are rejected',()=>{
 const {design,task,selection}=fixture();
 assert.throws(()=>specialistActivationRequest(design,task,{...selection,action:'actuate'},100),/Privileged/);
 const wrong=structuredClone(task);wrong.payload.modelId='other/model';
 assert.throws(()=>specialistActivationRequest(design,wrong,selection,100),/exactly match/);
 assert.throws(()=>executableReviewTasks({version:1,agents:[],tasks:[{id:'inert'}]}),/No executable/);
 assert.throws(()=>executableReviewTasks({version:1,agents:[],tasks:[task,task]}),/unique/);
});
