import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import test from 'node:test';
import {executableReviewTasks,specialistActivationRequest} from '../lib/specialist-activation';
import {createStarterDesign} from '../lib/specialist-design';
import type {Snapshot} from '../lib/graph';

const root=process.cwd().endsWith('/apps/web')?process.cwd().replace(/\/apps\/web$/,''):process.cwd();
const pythonBridge=String.raw`
import json, sys
from apexgraphswarm.control import ControlStore

request = json.load(sys.stdin)
now = 1000.0
store = ControlStore(":memory:", clock=lambda: now)
try:
    assignment = request["activation"]["assignment"]
    subject = store.enroll_worker(worker_id=assignment["workerId"],
                                 principal_id=assignment["principalId"], expires_at=1200)
    approver = store.enroll_worker(worker_id="worker:approver",
                                   principal_id="principal:approver", expires_at=1200)
    store.configure_specialist_approvers(["principal:approver"])
    store.configure_resource_capacity(assignment["resourceId"], 1)
    pending = store.create_specialist_contract(
        idempotency_key=request["activation"]["idempotencyKey"],
        design=request["activation"]["design"], assignment=assignment)
    contract_id = pending["contract"]["contractId"]
    store.approve_specialist_contract(contract_id, approver["workerId"], approver["credential"])
    active = store.activate_specialist_contract(contract_id)
    bound = store.bind_specialist_contract(contract_id=contract_id,
        plan=request["plan"], task_id=request["taskId"])["plan"]
    store.grant_access(principal_id=assignment["principalId"], tool_id=assignment["toolId"],
        resource_id=assignment["resourceId"], max_budget_microusd=request["budgetMicrousd"],
        expires_at=1200)
    run = store.create_run(bound, idempotency_key="typescript-contract-run",
                           budget_microusd=request["budgetMicrousd"])
    claimed = store.claim_authenticated(run["run"]["id"], assignment["workerId"],
        subject["credential"])
    bound_task = next(row for row in bound["tasks"] if row["id"] == request["taskId"])
    print(json.dumps({
        "contractStatus": active["contract"]["status"],
        "boundExecutionInputSha256": bound_task["payload"]["specialistAccess"]["executionInputSha256"],
        "claim": {
            "taskId": claimed["id"],
            "specialistContractId": claimed["specialistContractId"],
            "specialistAccessMatches": claimed["payload"]["specialistAccess"] == bound_task["payload"]["specialistAccess"],
            "executionInputMatches": claimed["payload"]["execution"]["input"] == assignment["executionInput"],
        },
    }, sort_keys=True))
finally:
    store.close()
`;

test('TypeScript activation request matches the Python ControlStore contract end to end',()=>{
 const graph:Snapshot={version:1,name:'Compiled graph-review fixture',nodes:[{id:'node-one',name:'One',kind:'file',path:'one.py',summary:'repository evidence fixture',confidence:'parsed'}],edges:[],warnings:[],truncated:false};
 const reservation=1000,model='review-model',modelId='fixture/reviewer-v1',resourceId=`model:${modelId}`,toolId='integration:openrouter:review';
 const compiledRaw=execFileSync('python3',['-m','apexgraphswarm.lab'],{
  cwd:root,encoding:'utf8',input:JSON.stringify({
   action:'compileDelegation',
   problem:{tasks:[{id:'source-review',duration_estimate:1,options:[{model,estimated_cost_microusd:reservation,duration_estimate:1}]}],budget_microusd:reservation,capacities:{[model]:1}},
   modelBindings:{[model]:{configured:true,adapterId:'openrouter',operation:'review',modelId,resourceId,toolId,costMicrousd:reservation,maxParallel:1}},
   taskInputs:{'source-review':{goal:'Review only this explicitly supplied graph snapshot.',graph,parameters:{maxOutputTokens:100}}},
  }),env:{...process.env,PYTHONDONTWRITEBYTECODE:'1'},
 });
 const compiled=JSON.parse(compiledRaw) as {plan:Record<string,any>;budgetMicrousd:number};
 const executable=executableReviewTasks(compiled);
 assert.equal(executable.length,1);
 const task=executable[0];

 const design=createStarterDesign(),specialist=design.agents.find(agent=>agent.id==='agent-reviewer')!,node=design.nodes[0];
 specialist.harnessId='openrouter';specialist.modelRef=modelId;
 specialist.policy.subjectRef='principal:typescript-specialist';
 specialist.policy.ownerRef='principal:workspace-owner';specialist.policy.tenantRef='tenant:fixture';
 specialist.policy.audience='apexgraphswarm';specialist.policy.purpose='review-graph';
 specialist.policy.actions=['read'];specialist.policy.resourceIds=[node.id];
 specialist.policy.ttlSeconds=100;specialist.policy.maxDelegationDepth=0;specialist.policy.approvalQuorum=1;
 specialist.tools=[{serverId:'review-gateway',toolName:'read-graph',gatewayId:'local-gateway'}];
 const selection={specialistId:specialist.id,nodeId:node.id,action:'read',workerId:'worker:typescript-specialist',mcpBinding:specialist.tools[0],idempotencyKey:'typescript-specialist-contract'};
 const activation=specialistActivationRequest(design,task,selection,1000);
 assert.deepEqual(activation.assignment.executionInput,task.payload.execution.input);

 const response=execFileSync('python3',['-c',pythonBridge],{
  cwd:root,encoding:'utf8',input:JSON.stringify({activation,plan:compiled.plan,taskId:task.id,budgetMicrousd:compiled.budgetMicrousd}),
  env:{...process.env,PYTHONDONTWRITEBYTECODE:'1'},
 });
 const result=JSON.parse(response) as {contractStatus:string;boundExecutionInputSha256:string;claim:{taskId:string;specialistContractId:string;specialistAccessMatches:boolean;executionInputMatches:boolean}};
 assert.equal(result.contractStatus,'active');
 assert.match(result.boundExecutionInputSha256,/^[a-f0-9]{64}$/);
 assert.equal(result.claim.taskId,task.id);
 assert.equal(result.claim.specialistContractId.length>0,true);
 assert.equal(result.claim.specialistAccessMatches,true);
 assert.equal(result.claim.executionInputMatches,true);
});
