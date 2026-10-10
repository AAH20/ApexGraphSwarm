import unittest

from apexgraphswarm.control import ControlError, ControlStore
from apexgraphswarm.delegation_plan import DelegationPlanError, compile_delegation_plan


MODEL = "vendor/model-small"


def problem(*, budget=10):
    return {
        "tasks": [
            {"id": "inspect", "dependencies": [], "duration_estimate": 1.0,
             "deadline": 8.0,
             "options": [{"model": MODEL, "estimated_cost_microusd": 5,
                          "duration_estimate": 2.0}]},
            {"id": "summarize", "dependencies": ["inspect"], "duration_estimate": 2.0,
             "deadline": 8.0,
             "options": [{"model": MODEL, "estimated_cost_microusd": 5,
                          "duration_estimate": 3.0}]},
        ],
        "budget_microusd": budget,
        "capacities": {MODEL: 2},
        "deadline_seconds": 10.0,
    }


def bindings():
    return {MODEL: {
        "configured": True,
        "adapterId": "openrouter",
        "operation": "review",
        "modelId": "vendor/model-small-2026-09",
        "resourceId": "model:vendor/model-small-2026-09",
        "toolId": "integration:openrouter:review",
        "costMicrousd": 5,
        "maxParallel": 2,
    }}


def review_graph(node_count=2):
    nodes = [{"id": f"n{index}", "name": f"file-{index}", "kind": "file",
              "path": f"src/file-{index}.py", "summary": f"Evidence {index}",
              "confidence": "parsed"} for index in range(node_count)]
    edges = ([{"source": "n0", "target": "n1", "relation": "imports",
               "confidence": "observed"}] if node_count > 1 else [])
    return {"version": 1, "name": "fixture-repository", "nodes": nodes,
            "edges": edges, "warnings": [], "truncated": False}


def task_inputs():
    return {"inspect": {"goal": " Inspect dependency evidence ", "graph": review_graph()},
            "summarize": {"goal": "Summarize verified findings", "graph": review_graph(),
                          "parameters": {"maxOutputTokens": 240}}}


class DelegationPlanTests(unittest.TestCase):
    def test_compile_recomputes_schedule_and_emits_control_compatible_dependencies(self):
        compiled = compile_delegation_plan(problem(), bindings())
        plan = compiled["plan"]
        self.assertEqual(len(plan["agents"]), 1)
        self.assertEqual(len(plan["tasks"]), 2)
        tasks = {task["payload"]["sourceTaskId"]: task for task in plan["tasks"]}
        self.assertEqual(tasks["summarize"]["dependencies"], [tasks["inspect"]["id"]])
        self.assertEqual(tasks["inspect"]["reservedCostMicrousd"], 5)
        self.assertEqual(tasks["summarize"]["maxAttempts"], 1)
        self.assertEqual(tasks["inspect"]["tool"], "integration:openrouter:review")
        self.assertEqual(tasks["inspect"]["resource"], "model:vendor/model-small-2026-09")
        self.assertEqual(tasks["inspect"]["payload"]["taskDurationEstimateSeconds"], 1.0)
        self.assertEqual(tasks["inspect"]["payload"]["durationEstimateSeconds"], 2.0)
        self.assertEqual(compiled["schedule"]["totalCostMicrousd"], 10)
        self.assertEqual(compiled["schedule"]["deadlineEstimateSeconds"], 10.0)
        self.assertIn("costs are caller estimates", " ".join(compiled["schedule"]["limits"]))
        self.assertTrue(compiled["schedule"]["dispatchPerformed"] is False)
        self.assertEqual(compiled["planMode"], "compile_only_metadata")
        self.assertNotIn("requireResourceCapacity", plan["tasks"][0])
        self.assertNotIn("execution", plan["tasks"][0]["payload"])
        self.assertEqual(len(compiled["sourceInputSha256"]), 64)
        self.assertEqual(len(compiled["planSha256"]), 64)
        self.assertEqual(compiled, compile_delegation_plan(problem(), bindings()))

    def test_compiled_plan_admits_only_with_exact_grant_and_claims_in_dag_order(self):
        compiled = compile_delegation_plan(problem(), bindings())
        with ControlStore(":memory:") as store:
            enrollment = store.enroll_worker(worker_id="model-worker", principal_id="principal",
                                             expires_at=store._now() + 1000)
            store.grant_access(principal_id="principal", tool_id="integration:openrouter:review",
                               resource_id="model:vendor/model-small-2026-09",
                               max_budget_microusd=10, expires_at=store._now() + 1000)
            run = store.create_run(compiled["plan"], idempotency_key="compiled-plan", budget_microusd=10)
            first = store.claim_authenticated(run["run"]["id"], "model-worker", enrollment["credential"])
            self.assertEqual(first["payload"]["sourceTaskId"], "inspect")
            self.assertEqual(first["tool"], "integration:openrouter:review")
            self.assertEqual(first["resource"], "model:vendor/model-small-2026-09")
            store.complete_authenticated(first["taskId"], first["leaseToken"],
                                         enrollment["credential"], {"fixture": True}, 5)
            second = store.claim_authenticated(run["run"]["id"], "model-worker", enrollment["credential"])
            self.assertEqual(second["payload"]["sourceTaskId"], "summarize")
            store.complete_authenticated(second["taskId"], second["leaseToken"],
                                         enrollment["credential"], {"fixture": True}, 5)
            status = store.status(run["run"]["id"])
            self.assertEqual(status["run"]["status"], "succeeded")
            self.assertEqual(status["run"]["spentMicrousd"], 10)

    def test_infeasible_unconfigured_and_inconsistent_mappings_fail_closed(self):
        with self.assertRaisesRegex(DelegationPlanError, "status=infeasible"):
            compile_delegation_plan(problem(budget=9), bindings())
        with self.assertRaisesRegex(DelegationPlanError, "no explicit configured adapter mapping"):
            compile_delegation_plan(problem(), {})
        wrong_tool = bindings()
        wrong_tool[MODEL]["toolId"] = "integration:openrouter:delegate"
        with self.assertRaisesRegex(DelegationPlanError, "toolId must exactly match"):
            compile_delegation_plan(problem(), wrong_tool)
        wrong_cost = bindings()
        wrong_cost[MODEL]["costMicrousd"] = 4
        with self.assertRaisesRegex(DelegationPlanError, "does not match its configured cost mapping"):
            compile_delegation_plan(problem(), wrong_cost)
        wrong_capacity = bindings()
        wrong_capacity[MODEL]["maxParallel"] = 1
        with self.assertRaisesRegex(DelegationPlanError, "exceeds its configured adapter capacity"):
            compile_delegation_plan(problem(), wrong_capacity)

    def test_caller_cannot_supply_or_substitute_a_precomputed_schedule(self):
        untrusted = problem()
        untrusted["schedule_result"] = {"status": "feasible", "assignments": []}
        with self.assertRaisesRegex(DelegationPlanError, "unsupported fields"):
            compile_delegation_plan(untrusted, bindings())
        malformed = problem()
        malformed["tasks"][1]["dependencies"] = ["missing"]
        with self.assertRaises(DelegationPlanError):
            compile_delegation_plan(malformed, bindings())

    def test_unknown_cost_schedule_cannot_be_compiled_as_a_known_reservation(self):
        unknown_cost = problem()
        unknown_cost["tasks"][0]["options"][0]["estimated_cost_microusd"] = None
        with self.assertRaisesRegex(DelegationPlanError, "status=unknown"):
            compile_delegation_plan(unknown_cost, bindings())

    def test_alias_model_ids_cannot_double_count_a_shared_capacity_pool(self):
        alias_problem = {
            "tasks": [
                {"id": "left", "options": [{"model": "alias-a", "estimated_cost_microusd": 2,
                                              "duration_estimate": 1}]},
                {"id": "right", "options": [{"model": "alias-b", "estimated_cost_microusd": 2,
                                               "duration_estimate": 1}]},
            ],
            "budget_microusd": 4,
            "capacities": {"alias-a": 1, "alias-b": 1},
        }
        shared = {"configured": True, "adapterId": "openrouter", "operation": "review",
                  "modelId": "vendor/model-small-2026-09",
                  "resourceId": "model:vendor/model-small-2026-09",
                  "toolId": "integration:openrouter:review", "costMicrousd": 2,
                  "maxParallel": 1}
        with self.assertRaisesRegex(DelegationPlanError, "share resource.*double-counted"):
            compile_delegation_plan(alias_problem,
                                    {"alias-a": shared, "alias-b": dict(shared)})

    def test_execution_mode_emits_pinned_bounded_review_input_and_capacity_requirement(self):
        compiled = compile_delegation_plan(problem(), bindings(), task_inputs=task_inputs())
        self.assertEqual(compiled["planMode"], "executable_review_plan")
        self.assertTrue(compiled["schedule"]["activationRequiresConfiguredResourceCapacity"])
        self.assertFalse(compiled["schedule"]["dispatchPerformed"])
        for task in compiled["plan"]["tasks"]:
            source_id = task["payload"]["sourceTaskId"]
            execution = task["payload"]["execution"]
            self.assertEqual(set(execution), {"version", "integrationId", "operation", "input"})
            self.assertEqual(execution["version"], 1)
            self.assertEqual(execution["integrationId"], "openrouter")
            self.assertEqual(execution["operation"], "review")
            self.assertEqual(execution["input"]["goal"], task_inputs()[source_id]["goal"].strip())
            self.assertEqual(execution["input"]["graph"], review_graph())
            expected_tokens = 240 if source_id == "summarize" else 600
            self.assertEqual(execution["input"]["parameters"]["maxOutputTokens"], expected_tokens)
            self.assertEqual(task["tool"], "integration:openrouter:review")
            self.assertEqual(task["resource"], "model:vendor/model-small-2026-09")
            self.assertTrue(task["requireResourceCapacity"])
            self.assertEqual(task["resourceConcurrencyLimit"], 2)

    def test_execution_plan_activation_requires_admin_capacity_and_caps_active_claims(self):
        parallel = problem()
        parallel["budget_microusd"] = 15
        parallel["tasks"][1]["dependencies"] = []
        parallel["tasks"].append({"id": "third", "dependencies": [], "duration_estimate": 1.0,
                                  "options": [{"model": MODEL, "estimated_cost_microusd": 5,
                                               "duration_estimate": 1.0}]})
        inputs = task_inputs()
        inputs["third"] = {"goal": "Review the third explicit task", "graph": review_graph()}
        compiled = compile_delegation_plan(parallel, bindings(), task_inputs=inputs)
        with ControlStore(":memory:") as store:
            with self.assertRaisesRegex(ControlError, "administrator-configured capacity"):
                store.create_run(compiled["plan"], idempotency_key="blocked-without-cap", budget_microusd=15)
            store.configure_resource_capacity("model:vendor/model-small-2026-09", 4)
            run = store.create_run(compiled["plan"], idempotency_key="enabled-after-cap", budget_microusd=15)
            enrollment = store.enroll_worker(worker_id="reviewer", principal_id="principal",
                                             expires_at=store._now() + 1000)
            store.grant_access(principal_id="principal", tool_id="integration:openrouter:review",
                               resource_id="model:vendor/model-small-2026-09",
                               max_budget_microusd=15, expires_at=store._now() + 1000)
            first = store.claim_authenticated(run["run"]["id"], "reviewer", enrollment["credential"])
            self.assertIsNotNone(first)
            self.assertEqual(first["resourceConcurrencyLimit"], 2)
            # The declared plan concurrency (2) is narrower than the admin cap (4).
            store.configure_resource_capacity("model:vendor/model-small-2026-09", 4)
            second = store.claim_authenticated(run["run"]["id"], "reviewer", enrollment["credential"])
            self.assertIsNotNone(second)
            self.assertEqual(second["resourceConcurrencyLimit"], 2)
            blocked = store.claim_authenticated(run["run"]["id"], "reviewer", enrollment["credential"])
            self.assertIsNone(blocked)

    def test_execution_input_mapping_must_exactly_cover_scheduled_tasks(self):
        with self.assertRaisesRegex(DelegationPlanError, "exactly cover"):
            compile_delegation_plan(problem(), bindings(), task_inputs={"inspect": task_inputs()["inspect"]})
        extra = task_inputs()
        extra["other"] = extra["inspect"]
        with self.assertRaisesRegex(DelegationPlanError, "exactly cover"):
            compile_delegation_plan(problem(), bindings(), task_inputs=extra)

    def test_review_payload_is_part_of_the_input_provenance_hash(self):
        first_inputs = task_inputs()
        second_inputs = task_inputs()
        second_inputs["inspect"]["goal"] = "A different explicit review goal"
        first = compile_delegation_plan(problem(), bindings(), task_inputs=first_inputs)
        second = compile_delegation_plan(problem(), bindings(), task_inputs=second_inputs)
        self.assertNotEqual(first["sourceInputSha256"], second["sourceInputSha256"])
        self.assertNotEqual(first["planSha256"], second["planSha256"])

    def test_execution_enabled_plan_rejects_non_review_binding_and_bad_graph(self):
        delegated = bindings()
        delegated[MODEL]["operation"] = "delegate"
        delegated[MODEL]["toolId"] = "integration:openrouter:delegate"
        with self.assertRaisesRegex(DelegationPlanError, "review bindings"):
            compile_delegation_plan(problem(), delegated, task_inputs=task_inputs())

        dangling = task_inputs()
        dangling["inspect"]["graph"] = {**review_graph(), "edges": [
            {"source": "n0", "target": "missing", "relation": "imports", "confidence": "parsed"}]}
        with self.assertRaisesRegex(DelegationPlanError, "dangling endpoint"):
            compile_delegation_plan(problem(), bindings(), task_inputs=dangling)

        unsupported = task_inputs()
        unsupported["inspect"]["hiddenPrompt"] = "do something else"
        with self.assertRaisesRegex(DelegationPlanError, "unsupported fields"):
            compile_delegation_plan(problem(), bindings(), task_inputs=unsupported)

        secret = task_inputs()
        secret["inspect"]["graph"]["summary"] = {"access_token": "should-not-persist"}
        with self.assertRaisesRegex(DelegationPlanError, "credential fields"):
            compile_delegation_plan(problem(), bindings(), task_inputs=secret)

    def test_execution_graph_and_output_limits_match_review_adapter(self):
        too_many = task_inputs()
        too_many["inspect"]["graph"] = review_graph(301)
        with self.assertRaisesRegex(DelegationPlanError, "at most 300 nodes"):
            compile_delegation_plan(problem(), bindings(), task_inputs=too_many)
        invalid_output = task_inputs()
        invalid_output["inspect"]["parameters"] = {"maxOutputTokens": 99}
        with self.assertRaisesRegex(DelegationPlanError, "from 100 to 600"):
            compile_delegation_plan(problem(), bindings(), task_inputs=invalid_output)


if __name__ == "__main__":
    unittest.main()
