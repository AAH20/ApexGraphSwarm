import unittest

from apexgraphswarm.control import AccessDenied, ControlError, ControlStore


class FakeClock:
    def __init__(self, value=1000.0):
        self.value = value

    def __call__(self):
        return self.value


def design(*, quorum=1, depth=0):
    return {
        "schemaVersion": 1, "id": "design-1", "name": "Reviewed design",
        "agents": [{"id": "specialist-1", "name": "Reviewer", "role": "Review graph evidence",
                    "harnessId": "openrouter", "modelRef": "vendor/model-a",
                    "skills": [{"id": "skill-review", "sourceUrl": "https://example.test/skill.md",
                                "revision": "rev-a", "sha256": "a" * 64}],
                    "tools": [{"serverId": "mcp-review", "toolName": "read-graph",
                               "gatewayId": "gateway-local"}],
                    "policy": {"provider": "external", "subjectRef": "principal-agent",
                               "ownerRef": "principal-owner", "tenantRef": "tenant-local",
                               "audience": "apexgraphswarm", "purpose": "review-graph",
                               "actions": ["read", "plan"], "resourceIds": ["node-repo"],
                               "ttlSeconds": 100, "maxDelegationDepth": depth,
                               "approvalQuorum": quorum}}],
        "teams": [{"id": "team-review", "name": "Reviewers", "agentIds": ["specialist-1"]}],
        "nodes": [{"id": "node-workspace", "label": "Workspace", "kind": "workspace",
                   "parentId": None, "teamIds": [], "externalRef": "workspace:local"},
                  {"id": "node-repo", "label": "Repository", "kind": "repository",
                   "parentId": "node-workspace", "teamIds": ["team-review"],
                   "externalRef": "repo:sample"}],
    }


def execution_input():
    return {"goal": "Review the selected graph snapshot.",
            "graph": {"version": 1, "name": "sample", "nodes": [], "edges": []},
            "parameters": {"maxOutputTokens": 600}}


def assignment(store, *, worker="worker-agent", expires=1090.0):
    return {"specialistId": "specialist-1", "nodeId": "node-repo",
            "action": "read", "audience": "apexgraphswarm", "purpose": "review-graph",
            "workerId": worker, "principalId": "principal-agent",
            "logicalAgentId": "logical-agent", "modelId": "vendor/model-a",
            "adapterId": "openrouter", "toolId": "integration:openrouter:review",
            "resourceId": "model:vendor/model-a",
            "mcpBinding": {"serverId": "mcp-review", "toolName": "read-graph",
                           "gatewayId": "gateway-local"},
            "expiresAt": expires, "executionInput": execution_input()}


def plan(contract_id=None, *, graph=None, logical_agent="logical-agent"):
    graph_input = execution_input() if graph is None else graph
    payload = {"sourceTaskId": "source-1", "modelId": "vendor/model-a",
               "adapterId": "openrouter", "operation": "review",
               "execution": {"version": 1, "integrationId": "openrouter",
                             "operation": "review", "input": graph_input}}
    task = {"id": "review-task", "agentId": logical_agent, "dependencies": [],
            "payload": payload, "reservedCostMicrousd": 10, "maxAttempts": 1,
            "executionClass": "external", "tool": "integration:openrouter:review",
            "resource": "model:vendor/model-a", "requireResourceCapacity": True,
            "resourceConcurrencyLimit": 1}
    if contract_id:
        task["specialistContractId"] = contract_id
    return {"version": 1, "agents": [{"id": "logical-agent", "name": "Review worker"}],
            "tasks": [task]}


class SpecialistAccessTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.store = ControlStore(":memory:", clock=self.clock)
        self.subject = self.store.enroll_worker(worker_id="worker-agent", principal_id="principal-agent",
                                                expires_at=1200)
        self.approver_a = self.store.enroll_worker(worker_id="worker-approver-a", principal_id="principal-a",
                                                   expires_at=1200)
        self.approver_b = self.store.enroll_worker(worker_id="worker-approver-b", principal_id="principal-b",
                                                   expires_at=1200)
        self.store.configure_specialist_approvers(["principal-a", "principal-b"])
        self.store.configure_resource_capacity("model:vendor/model-a", 1)

    def tearDown(self):
        self.store.close()

    def contract(self, *, key="contract-1", source=None, chosen=None):
        return self.store.create_specialist_contract(idempotency_key=key,
                                                     design=design() if source is None else source,
                                                     assignment=assignment(self.store) if chosen is None else chosen)

    def approve_and_activate(self, result):
        contract_id = result["contract"]["contractId"]
        self.store.approve_specialist_contract(contract_id, "worker-approver-a",
                                               self.approver_a["credential"])
        return self.store.activate_specialist_contract(contract_id)

    def test_authenticated_quorum_and_immutable_review_artifact(self):
        pending = self.contract(source=design(quorum=2))
        contract_id = pending["contract"]["contractId"]
        self.assertEqual(pending["contract"]["status"], "pending_approval")
        self.assertEqual(pending["contract"]["executionInput"], execution_input())
        self.assertEqual(len(pending["contract"]["designSha256"]), 64)
        with self.assertRaisesRegex(ControlError, "quorum"):
            self.store.activate_specialist_contract(contract_id)
        with self.assertRaises(AccessDenied):
            self.store.approve_specialist_contract(contract_id, "worker-agent",
                                                   self.subject["credential"])
        self.store.approve_specialist_contract(contract_id, "worker-approver-a",
                                               self.approver_a["credential"])
        with self.assertRaisesRegex(ControlError, "quorum"):
            self.store.activate_specialist_contract(contract_id)
        self.store.approve_specialist_contract(contract_id, "worker-approver-b",
                                               self.approver_b["credential"])
        active = self.store.activate_specialist_contract(contract_id)
        self.assertEqual(active["contract"]["status"], "active")
        self.assertEqual(active["recordedApprovalCount"], 2)
        self.assertEqual(active["validApprovalCount"], 2)
        self.assertTrue(active["quorumSatisfied"])
        self.assertIn("reviewedDesign", active["contract"])
        self.assertEqual(active["contract"]["operation"], "review")

    def test_binding_requires_exact_execution_snapshot_and_dispatch_scope(self):
        active = self.approve_and_activate(self.contract())
        contract_id = active["contract"]["contractId"]
        compiled = plan()
        bound = self.store.bind_specialist_contract(contract_id=contract_id,
                                                    plan=compiled, task_id="review-task")["plan"]
        self.assertEqual(bound["tasks"][0]["payload"]["specialistAccess"]["executionInputSha256"],
                         active["contract"]["executionInputSha256"])
        run = self.store.create_run(bound, idempotency_key="specialist-run", budget_microusd=10)
        self.store.grant_access(principal_id="principal-agent", tool_id="integration:openrouter:review",
                                resource_id="model:vendor/model-a", max_budget_microusd=10,
                                expires_at=1200)
        claimed = self.store.claim_authenticated(run["run"]["id"], "worker-agent",
                                                 self.subject["credential"])
        self.assertEqual(claimed["specialistContractId"], contract_id)
        self.assertEqual(claimed["payload"]["specialistAccess"],
                         bound["tasks"][0]["payload"]["specialistAccess"])

        substituted = plan(graph={"goal": "different"})
        with self.assertRaisesRegex(ControlError, "execution input"):
            self.store.bind_specialist_contract(contract_id=contract_id,
                                                plan=substituted, task_id="review-task")
        changed = bound
        changed["tasks"][0]["payload"]["execution"]["operation"] = "write"
        with self.assertRaisesRegex(ControlError, "review operation"):
            self.store.create_run(changed, idempotency_key="mutated-operation", budget_microusd=10)

    def test_contract_revocation_blocks_heartbeat_and_task_needs_rebinding(self):
        active = self.approve_and_activate(self.contract())
        contract_id = active["contract"]["contractId"]
        bound = self.store.bind_specialist_contract(contract_id=contract_id,
                                                    plan=plan(), task_id="review-task")["plan"]
        run = self.store.create_run(bound, idempotency_key="revocation-run", budget_microusd=10)
        self.store.grant_access(principal_id="principal-agent", tool_id="integration:openrouter:review",
                                resource_id="model:vendor/model-a", max_budget_microusd=10,
                                expires_at=1200)
        claimed = self.store.claim_authenticated(run["run"]["id"], "worker-agent",
                                                 self.subject["credential"])
        self.store.revoke_specialist_contract(contract_id)
        with self.assertRaisesRegex(AccessDenied, "not active"):
            self.store.heartbeat_authenticated(claimed["taskId"], claimed["leaseToken"],
                                               self.subject["credential"])

    def test_expired_worker_or_contract_cannot_claim_and_contract_scope_is_fail_closed(self):
        invalid_depth = design(depth=1)
        with self.assertRaisesRegex(ControlError, "depth 0"):
            self.contract(key="depth", source=invalid_depth)
        invalid_action = assignment(self.store)
        invalid_action["action"] = "actuate"
        with self.assertRaisesRegex(ControlError, "read or plan"):
            self.contract(key="actuate", chosen=invalid_action)
        wrong_subject = assignment(self.store)
        wrong_subject["principalId"] = "forged-principal"
        with self.assertRaisesRegex(ControlError, "subjectRef"):
            self.contract(key="principal", chosen=wrong_subject)

        pending = self.contract(key="expires")
        self.approve_and_activate(pending)
        self.clock.value = 1091
        with self.assertRaisesRegex(ControlError, "expired"):
            self.store.bind_specialist_contract(contract_id=pending["contract"]["contractId"],
                                                plan=plan(), task_id="review-task")
        replay = self.contract(key="expires")
        self.assertEqual(replay["contract"]["contractId"], pending["contract"]["contractId"])
        self.assertTrue(replay["contract"]["expired"])
        changed = assignment(self.store)
        changed["executionInput"] = {**execution_input(), "goal": "changed after issue"}
        with self.assertRaisesRegex(ControlError, "idempotency key"):
            self.contract(key="expires", chosen=changed)

    def test_allowlist_removal_demotes_contract_and_does_not_resurrect_approval(self):
        pending = self.contract()
        contract_id = pending["contract"]["contractId"]
        self.store.approve_specialist_contract(contract_id, "worker-approver-a",
                                               self.approver_a["credential"])
        self.store.approve_specialist_contract(contract_id, "worker-approver-b",
                                               self.approver_b["credential"])
        active = self.store.activate_specialist_contract(contract_id)
        self.assertEqual(active["contract"]["status"], "active")
        self.store.configure_specialist_approvers(["principal-b"])
        status = self.store.specialist_contract_status(contract_id)
        self.assertEqual(status["contract"]["status"], "pending_approval")
        self.assertEqual({entry["principalId"] for entry in status["approvals"]}, {"principal-b"})
        self.store.configure_specialist_approvers(["principal-a", "principal-b"])
        status = self.store.specialist_contract_status(contract_id)
        self.assertEqual({entry["principalId"] for entry in status["approvals"]}, {"principal-b"})


if __name__ == "__main__":
    unittest.main()
