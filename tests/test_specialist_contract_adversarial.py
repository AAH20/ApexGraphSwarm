"""Adversarial checks for opt-in specialist contract enforcement."""
import copy
import unittest

from apexgraphswarm.access import AccessDenied
from apexgraphswarm.control import ControlError, ControlStore
from apexgraphswarm.specialist_access import SpecialistContractError


class FakeClock:
    def __init__(self, value=20_000.0):
        self.value = value

    def __call__(self):
        return self.value


class SpecialistContractAdversarialTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.store = ControlStore(":memory:", clock=self.clock)
        self.expiry = self.clock.value + 500
        self.subject = self.store.enroll_worker(worker_id="subject-worker", principal_id="principal:subject",
                                                expires_at=self.expiry)
        self.approver_a = self.store.enroll_worker(worker_id="approver-worker-a", principal_id="principal:reviewer-a",
                                                   expires_at=self.expiry)
        self.approver_a_shadow = self.store.enroll_worker(worker_id="approver-worker-a-shadow", principal_id="principal:reviewer-a",
                                                          expires_at=self.expiry)
        self.approver_b = self.store.enroll_worker(worker_id="approver-worker-b", principal_id="principal:reviewer-b",
                                                   expires_at=self.expiry)
        self.unlisted = self.store.enroll_worker(worker_id="unlisted-worker", principal_id="principal:unlisted",
                                                 expires_at=self.expiry)
        self.store.configure_specialist_approvers(["principal:reviewer-a", "principal:reviewer-b"])
        self.design = self.make_design()
        self.assignment = self.make_assignment()

    def tearDown(self):
        self.store.close()

    @staticmethod
    def make_design():
        binding = {"serverId": "mcp-server-local", "toolName": "review_graph", "gatewayId": "gateway-local"}
        return {
            "schemaVersion": 1,
            "id": "design-fixture",
            "name": "Fixture design",
            "agents": [{
                "id": "agent-reviewer", "name": "Reviewer", "role": "Review bounded graph evidence.",
                "harnessId": "openrouter", "modelRef": "test/model", "skills": [], "tools": [binding],
                "policy": {"provider": "external", "subjectRef": "principal:subject",
                           "ownerRef": "principal:owner", "tenantRef": "tenant:fixture",
                           "audience": "apexgraphswarm", "purpose": "graph-review",
                           "actions": ["read", "plan"], "resourceIds": ["node-repository"],
                           "ttlSeconds": 60, "maxDelegationDepth": 0, "approvalQuorum": 2},
            }],
            "teams": [{"id": "team-review", "name": "Review team", "agentIds": ["agent-reviewer"]}],
            "nodes": [
                {"id": "workspace-main", "label": "Workspace", "kind": "workspace", "parentId": None,
                 "teamIds": ["team-review"], "externalRef": "workspace:fixture"},
                {"id": "node-repository", "label": "Repository", "kind": "repository", "parentId": "workspace-main",
                 "teamIds": ["team-review"], "externalRef": "repository:fixture"},
            ],
        }

    def make_assignment(self):
        return {
            "specialistId": "agent-reviewer", "nodeId": "node-repository", "action": "read",
            "audience": "apexgraphswarm", "purpose": "graph-review", "workerId": "subject-worker",
            "principalId": "principal:subject", "logicalAgentId": "logical-reviewer",
            "modelId": "test/model", "adapterId": "openrouter",
            "toolId": "integration:openrouter:review", "resourceId": "model:test/model",
            "mcpBinding": {"serverId": "mcp-server-local", "toolName": "review_graph", "gatewayId": "gateway-local"},
            "expiresAt": self.clock.value + 45,
            "executionInput": {"goal": "Review the fixture graph only.",
                                "graph": {"version": 1, "name": "fixture", "nodes": [], "edges": []},
                                "parameters": {"maxOutputTokens": 100}},
        }

    def new_contract(self, *, suffix="one", design=None, assignment=None):
        return self.store.create_specialist_contract(
            idempotency_key=f"specialist-contract-{suffix}",
            design=copy.deepcopy(self.design if design is None else design),
            assignment=copy.deepcopy(self.assignment if assignment is None else assignment),
        )

    def approve_and_activate(self, contract_id):
        self.store.approve_specialist_contract(contract_id, "approver-worker-a", self.approver_a["credential"])
        self.store.approve_specialist_contract(contract_id, "approver-worker-b", self.approver_b["credential"])
        return self.store.activate_specialist_contract(contract_id)

    def make_plan(self, contract_id, *, execution_input=None, logical_agent="logical-reviewer"):
        value = copy.deepcopy(self.assignment["executionInput"] if execution_input is None else execution_input)
        return {"version": 1, "agents": [{"id": logical_agent, "name": "Reviewer"}], "tasks": [{
            "id": "review-task", "agentId": logical_agent, "dependencies": [],
                "payload": {"modelId": "test/model", "adapterId": "openrouter",
                        "operation": "review",
                        "execution": {"version": 1, "integrationId": "openrouter", "operation": "review", "input": value}},
            "reservedCostMicrousd": 10, "maxAttempts": 1, "executionClass": "external",
            "tool": "integration:openrouter:review", "resource": "model:test/model",
            "requireResourceCapacity": True, "resourceConcurrencyLimit": 1,
            "specialistContractId": contract_id,
        }]}

    def active_bound_run(self):
        contract = self.new_contract(suffix="run")
        self.approve_and_activate(contract["contract"]["contractId"])
        bound = self.store.bind_specialist_contract(contract_id=contract["contract"]["contractId"],
                                                    plan=self.make_plan(contract["contract"]["contractId"]),
                                                    task_id="review-task")
        self.store.configure_resource_capacity("model:test/model", 1)
        self.store.grant_access(principal_id="principal:subject", tool_id="integration:openrouter:review",
                                resource_id="model:test/model", max_budget_microusd=100,
                                expires_at=self.expiry)
        run = self.store.create_run(bound["plan"], idempotency_key="specialist-bound-run", budget_microusd=10)
        task = run["tasks"][0]
        return contract["contract"]["contractId"], run, task

    def test_approval_identity_is_derived_from_worker_credentials(self):
        contract = self.new_contract(suffix="derived-identity")["contract"]["contractId"]
        # A caller cannot name an approver principal in the approval method.
        with self.assertRaises(TypeError):
            self.store.approve_specialist_contract(contract, "unlisted-worker", self.unlisted["credential"],
                                                   principal_id="principal:reviewer-a")
        # Supplying an allowed worker ID with somebody else's token does not forge an approval.
        with self.assertRaises(AccessDenied):
            self.store.approve_specialist_contract(contract, "approver-worker-a", self.unlisted["credential"])
        # Even an allowlisted target subject cannot approve its own contract.
        self.store.configure_specialist_approvers(["principal:subject", "principal:reviewer-b"])
        with self.assertRaises(AccessDenied):
            self.store.approve_specialist_contract(contract, "subject-worker", self.subject["credential"])
        state = self.store.specialist_contract_status(contract)
        self.assertEqual(state["recordedApprovalCount"], 0)
        self.assertEqual(state["validApprovalCount"], 0)
        self.assertFalse(state["quorumSatisfied"])

    def test_duplicate_workers_for_one_principal_do_not_satisfy_quorum(self):
        self.store.configure_specialist_approvers(["principal:reviewer-a", "principal:reviewer-b"])
        contract = self.new_contract(suffix="unique-principals")["contract"]["contractId"]
        self.store.approve_specialist_contract(contract, "approver-worker-a", self.approver_a["credential"])
        self.store.approve_specialist_contract(contract, "approver-worker-a-shadow", self.approver_a_shadow["credential"])
        state = self.store.specialist_contract_status(contract)
        self.assertEqual(state["recordedApprovalCount"], 1)
        self.assertEqual(state["validApprovalCount"], 1)
        self.assertFalse(state["quorumSatisfied"])
        self.assertEqual({item["principalId"] for item in state["approvals"]}, {"principal:reviewer-a"})
        with self.assertRaisesRegex(ControlError, "quorum"):
            self.store.activate_specialist_contract(contract)
        self.store.approve_specialist_contract(contract, "approver-worker-b", self.approver_b["credential"])
        state = self.store.specialist_contract_status(contract)
        self.assertEqual(state["validApprovalCount"], 2)
        self.assertTrue(state["quorumSatisfied"])
        self.assertEqual(self.store.activate_specialist_contract(contract)["contract"]["status"], "active")

    def test_approver_allowlist_change_requires_fresh_quorum_without_resurrecting_votes(self):
        contract = self.new_contract(suffix="allowlist-revision")["contract"]["contractId"]
        self.store.approve_specialist_contract(contract, "approver-worker-a", self.approver_a["credential"])
        self.store.approve_specialist_contract(contract, "approver-worker-b", self.approver_b["credential"])
        self.store.activate_specialist_contract(contract)
        self.store.configure_specialist_approvers(["principal:reviewer-b"])
        state = self.store.specialist_contract_status(contract)
        self.assertEqual(state["contract"]["status"], "pending_approval")
        self.assertEqual(state["recordedApprovalCount"], 1)
        self.assertEqual(state["validApprovalCount"], 1)
        self.assertFalse(state["quorumSatisfied"])
        self.store.configure_specialist_approvers(["principal:reviewer-a", "principal:reviewer-b"])
        # Re-adding a removed principal must not revive its old vote.
        state = self.store.specialist_contract_status(contract)
        self.assertEqual(state["contract"]["status"], "pending_approval")
        self.assertEqual(state["recordedApprovalCount"], 1)
        self.assertEqual(state["validApprovalCount"], 1)
        self.assertFalse(state["quorumSatisfied"])
        with self.assertRaisesRegex(ControlError, "quorum"):
            self.store.activate_specialist_contract(contract)
        self.store.approve_specialist_contract(contract, "approver-worker-a", self.approver_a["credential"])
        self.assertTrue(self.store.specialist_contract_status(contract)["quorumSatisfied"])
        self.assertEqual(self.store.activate_specialist_contract(contract)["contract"]["status"], "active")

    def test_contract_requires_exact_agent_node_assignment_and_policy_scope(self):
        unassigned = copy.deepcopy(self.design)
        unassigned["nodes"][1]["teamIds"] = []
        with self.assertRaisesRegex(ControlError, "exact scope node"):
            self.new_contract(suffix="unassigned-node", design=unassigned)
        parent_assignment = copy.deepcopy(self.assignment)
        parent_assignment["nodeId"] = "workspace-main"
        with self.assertRaisesRegex(ControlError, "resource allowlist"):
            self.new_contract(suffix="parent-inheritance", assignment=parent_assignment)
        missing_agent = copy.deepcopy(self.design)
        missing_agent["teams"][0]["agentIds"] = []
        with self.assertRaisesRegex(ControlError, "exact scope node"):
            self.new_contract(suffix="unassigned-agent", design=missing_agent)
        wrong_worker = copy.deepcopy(self.assignment)
        wrong_worker["workerId"] = "approver-worker-a"
        wrong_worker["principalId"] = "principal:reviewer-a"
        with self.assertRaisesRegex(ControlError, "principal must exactly match"):
            self.new_contract(suffix="wrong-subject-worker", assignment=wrong_worker)

    def test_contract_rejects_ttl_expiry_delegation_and_adapter_substitution(self):
        too_long = copy.deepcopy(self.assignment)
        too_long["expiresAt"] = self.clock.value + 61
        with self.assertRaisesRegex(ControlError, "policy TTL"):
            self.new_contract(suffix="ttl-bound", assignment=too_long)
        expired = copy.deepcopy(self.assignment)
        expired["expiresAt"] = self.clock.value
        with self.assertRaisesRegex(ControlError, "policy TTL"):
            self.new_contract(suffix="expired", assignment=expired)
        delegated = copy.deepcopy(self.design)
        delegated["agents"][0]["policy"]["maxDelegationDepth"] = 1
        with self.assertRaisesRegex(ControlError, "delegation depth 0"):
            self.new_contract(suffix="delegation-depth", design=delegated)
        wrong_adapter = copy.deepcopy(self.assignment)
        wrong_adapter["adapterId"] = "another-adapter"
        with self.assertRaisesRegex(ControlError, "Model and adapter"):
            self.new_contract(suffix="adapter-binding", assignment=wrong_adapter)

    def test_execution_input_and_logical_agent_cannot_be_substituted_after_review(self):
        contract = self.new_contract(suffix="input-binding")["contract"]["contractId"]
        self.approve_and_activate(contract)
        changed = copy.deepcopy(self.assignment["executionInput"])
        changed["goal"] = "Read a different scope."
        with self.assertRaisesRegex(ControlError, "execution input"):
            self.store.bind_specialist_contract(contract_id=contract, plan=self.make_plan(contract, execution_input=changed),
                                                task_id="review-task")
        with self.assertRaisesRegex(ControlError, "agent, tool, or resource"):
            self.store.bind_specialist_contract(contract_id=contract, plan=self.make_plan(contract, logical_agent="other-agent"),
                                                task_id="review-task")
        good = self.store.bind_specialist_contract(contract_id=contract, plan=self.make_plan(contract), task_id="review-task")
        access = good["plan"]["tasks"][0]["payload"]["specialistAccess"]
        self.assertEqual(access["executionInputSha256"], good["executionInputSha256"])

    def test_bound_task_requires_exact_worker_and_revocation_blocks_heartbeat(self):
        contract_id, run, task = self.active_bound_run()
        run_id, task_id = run["run"]["id"], task["taskId"]
        with self.assertRaises(AccessDenied):
            self.store.claim_authenticated(run_id, "approver-worker-a", self.approver_a["credential"],
                                           task_id=task_id)
        claimed = self.store.claim_authenticated(run_id, "subject-worker", self.subject["credential"],
                                                  task_id=task_id, lease_seconds=10)
        self.assertEqual(claimed["taskId"], task_id)
        self.assertEqual(claimed["specialistContractId"], contract_id)
        with self.assertRaises(AccessDenied):
            self.store.heartbeat_authenticated(task_id, claimed["leaseToken"], self.approver_a["credential"])
        self.store.revoke_specialist_contract(contract_id)
        with self.assertRaisesRegex(AccessDenied, "not active|approval quorum"):
            self.store.heartbeat_authenticated(task_id, claimed["leaseToken"], self.subject["credential"])
        status = self.store.status(run_id)
        self.assertEqual(status["tasks"][0]["status"], "running")
        self.assertGreater(status["run"]["reservedMicrousd"], 0)

    def test_contract_expiry_blocks_claim_even_if_previous_approval_was_valid(self):
        contract = self.new_contract(suffix="ttl-claim")
        self.approve_and_activate(contract["contract"]["contractId"])
        self.store.bind_specialist_contract(contract_id=contract["contract"]["contractId"],
                                            plan=self.make_plan(contract["contract"]["contractId"]),
                                            task_id="review-task")
        self.store.configure_resource_capacity("model:test/model", 1)
        self.store.grant_access(principal_id="principal:subject", tool_id="integration:openrouter:review",
                                resource_id="model:test/model", max_budget_microusd=100,
                                expires_at=self.expiry)
        run = self.store.create_run(self.store.bind_specialist_contract(
            contract_id=contract["contract"]["contractId"], plan=self.make_plan(contract["contract"]["contractId"]),
            task_id="review-task")["plan"], idempotency_key="expired-specialist-run", budget_microusd=10)
        # Store API time is authoritative; assignment input never supplies elapsedSeconds.
        self.clock.value += 46
        with self.assertRaises(AccessDenied):
            self.store.claim_authenticated(run["run"]["id"], "subject-worker", self.subject["credential"],
                                           task_id=run["tasks"][0]["taskId"])


if __name__ == "__main__":
    unittest.main()
