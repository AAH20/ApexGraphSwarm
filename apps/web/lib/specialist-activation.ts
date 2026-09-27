import {validateSpecialistDesign,previewSpecialistAccess,type SpecialistDesign,type ToolBinding} from './specialist-design';
import {parseSnapshot} from './graph';
type Row=Record<string,any>;
const record=(value:unknown):value is Row=>!!value&&typeof value==='object'&&!Array.isArray(value);
export type ExecutableReviewTask={id:string;agentId:string;tool:string;resource:string;payload:Row};
export function executableReviewTasks(value:unknown):ExecutableReviewTask[]{
 if(!record(value))throw Error('Import a compiled plan or Optimization Lab evidence export.');
 const plan=record(value.result)&&record(value.result.plan)?value.result.plan:record(value.plan)?value.plan:value;
 if(plan.version!==1||!Array.isArray(plan.tasks)||!Array.isArray(plan.agents)||plan.tasks.length>300)throw Error('A version 1 plan with at most 300 tasks is required.');
 if(new TextEncoder().encode(JSON.stringify(plan)).length>1048576)throw Error('Compiled plan exceeds 1 MiB.');
 const tasks=plan.tasks.filter((task:unknown)=>record(task)&&task.executionClass==='external'&&task.requireResourceCapacity===true&&record(task.payload)&&record(task.payload.execution)&&task.payload.execution.version===1);
 if(!tasks.length)throw Error('No executable review tasks found. Compile with explicit taskInputs first.');
 const ids=new Set<string>();
 for(const task of tasks){
  if(typeof task.id!=='string'||ids.has(task.id)||typeof task.agentId!=='string'||typeof task.tool!=='string'||typeof task.resource!=='string')throw Error('Each imported task needs unique exact identities and scope.');
  ids.add(task.id);
  const execution=task.payload.execution;
  if(!['openrouter','vllm'].includes(execution.integrationId)||execution.operation!=='review'||!record(execution.input))throw Error('Only executable OpenRouter/vLLM review tasks are supported.');
  parseSnapshot(execution.input.graph);
 }
 return tasks;
}
export function specialistActivationRequest(design:SpecialistDesign,task:ExecutableReviewTask,selection:{specialistId:string;nodeId:string;action:string;workerId:string;mcpBinding:ToolBinding;idempotencyKey:string},nowSeconds=Date.now()/1000){
 const validation=validateSpecialistDesign(design);
 if(!validation.valid||!validation.design)throw Error(validation.errors.slice(0,3).join(' '));
 const safe=validation.design,agent=safe.agents.find(item=>item.id===selection.specialistId);
 if(!agent)throw Error('Select a specialist in this design.');
 const preview=previewSpecialistAccess(safe,{agentId:agent.id,nodeId:selection.nodeId,action:selection.action,audience:agent.policy.audience,purpose:agent.policy.purpose,elapsedSeconds:0,approverIds:[]});
 if(preview.decision==='denied')throw Error(preview.reasons.join(' '));
 if(!/^[A-Za-z0-9][A-Za-z0-9_.:@/-]{0,127}$/.test(selection.workerId))throw Error('Enter the exact enrolled worker ID.');
 if(!Number.isFinite(nowSeconds)||nowSeconds<0)throw Error('A valid issue time is required.');
 const binding=selection.mcpBinding;
 if(!agent.tools.some(tool=>tool.serverId===binding.serverId&&tool.toolName===binding.toolName&&tool.gatewayId===binding.gatewayId))throw Error('Choose an exact tool declaration belonging to this specialist.');
 const payload=task.payload,execution=payload.execution;
 if(!record(execution)||execution.version!==1||!record(execution.input)||!['openrouter','vllm'].includes(execution.integrationId)||execution.operation!=='review')throw Error('A compiled executable review is required.');
 if(payload.modelId!==agent.modelRef||payload.adapterId!==agent.harnessId||execution.integrationId!==agent.harnessId||payload.operation!=='review'||task.tool!==`integration:${agent.harnessId}:review`)throw Error('The specialist model and execution adapter must exactly match the imported task.');
 const request={action:'createSpecialistContract',idempotencyKey:selection.idempotencyKey,design:safe,assignment:{specialistId:agent.id,nodeId:selection.nodeId,action:selection.action,audience:agent.policy.audience,purpose:agent.policy.purpose,workerId:selection.workerId,principalId:agent.policy.subjectRef,logicalAgentId:task.agentId,modelId:agent.modelRef,adapterId:agent.harnessId,toolId:task.tool,resourceId:task.resource,mcpBinding:binding,expiresAt:Math.floor(nowSeconds+agent.policy.ttlSeconds),executionInput:execution.input}};
 if(new TextEncoder().encode(JSON.stringify(request)).length>1500000)throw Error('Activation request exceeds 1.5 MB.');
 return request;
}
