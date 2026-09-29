"""Tests for saga transactions."""
import unittest

from kernels.agent_hypervisor.saga import (
    Saga, SagaError, SagaLog, SagaOrchestrator, SagaState, SagaStep,
)


class SagaStepTests(unittest.TestCase):
    def test_step_to_dict(self):
        step = SagaStep(name="test", action=lambda: None)
        data = step.to_dict()
        self.assertEqual(data["name"], "test")
        self.assertFalse(data["compensated"])
        self.assertFalse(data["failed"])


class SagaTests(unittest.TestCase):
    def test_empty_saga_completes(self):
        saga = Saga("empty")
        results = saga.execute()
        self.assertEqual(results, [])
        self.assertEqual(saga.state, SagaState.COMPLETED)

    def test_single_step_saga(self):
        saga = Saga("single")
        saga.add_step("step1", lambda: 42)
        results = saga.execute()
        self.assertEqual(results, [42])
        self.assertEqual(saga.state, SagaState.COMPLETED)

    def test_multi_step_saga(self):
        saga = Saga("multi")
        saga.add_step("step1", lambda: 1)
        saga.add_step("step2", lambda: 2)
        saga.add_step("step3", lambda: 3)
        results = saga.execute()
        self.assertEqual(results, [1, 2, 3])
        self.assertEqual(saga.state, SagaState.COMPLETED)

    def test_step_failure_triggers_compensation(self):
        compensated = []

        def action1():
            return "result1"

        def comp1():
            compensated.append("comp1")

        def action2():
            raise RuntimeError("step2 failed")

        saga = Saga("failing")
        saga.add_step("step1", action1, comp1)
        saga.add_step("step2", action2)

        with self.assertRaises(SagaError):
            saga.execute()

        self.assertEqual(saga.state, SagaState.COMPENSATED)
        self.assertEqual(compensated, ["comp1"])

    def test_compensation_order_is_reverse(self):
        compensated = []

        saga = Saga("reverse-order")
        saga.add_step("s1", lambda: 1, lambda: compensated.append("c1"))
        saga.add_step("s2", lambda: 2, lambda: compensated.append("c2"))
        saga.add_step("s3", lambda: 3, lambda: compensated.append("c3"))
        saga.add_step("s4", lambda: (_ for _ in ()).throw(RuntimeError("fail")))

        with self.assertRaises(SagaError):
            saga.execute()

        self.assertEqual(compensated, ["c3", "c2", "c1"])

    def test_compensation_error_marks_failed(self):
        def bad_compensation():
            raise RuntimeError("compensation failed")

        saga = Saga("bad-comp")
        saga.add_step("s1", lambda: 1, bad_compensation)
        saga.add_step("s2", lambda: (_ for _ in ()).throw(RuntimeError("fail")))

        with self.assertRaises(SagaError) as ctx:
            saga.execute()

        self.assertEqual(saga.state, SagaState.FAILED)
        self.assertIn("compensation", str(ctx.exception).lower())

    def test_cannot_add_steps_after_start(self):
        saga = Saga("started")
        saga.add_step("s1", lambda: 1)
        saga.execute()
        with self.assertRaises(SagaError):
            saga.add_step("s2", lambda: 2)

    def test_cannot_execute_twice(self):
        saga = Saga("once")
        saga.add_step("s1", lambda: 1)
        saga.execute()
        with self.assertRaises(SagaError):
            saga.execute()

    def test_saga_with_metadata(self):
        saga = Saga("meta", metadata={"agent": "test-agent", "task": "deploy"})
        saga.add_step("s1", lambda: "done")
        saga.execute()
        self.assertEqual(saga.log.metadata["agent"], "test-agent")

    def test_saga_to_dict(self):
        saga = Saga("dict-test")
        saga.add_step("s1", lambda: 1)
        saga.execute()
        data = saga.to_dict()
        self.assertEqual(data["name"], "dict-test")
        self.assertEqual(data["state"], "completed")
        self.assertIn("steps", data)
        self.assertIn("log", data)


class SagaLogTests(unittest.TestCase):
    def test_log_records_events(self):
        log = SagaLog(saga_id="test-123")
        log.record_step_start("s1")
        log.record_step_complete("s1", "result")
        log.record_step_compensation("s1")
        log.record_step_compensated("s1")

        self.assertEqual(len(log.steps), 4)
        self.assertEqual(log.steps[0]["event"], "start")
        self.assertEqual(log.steps[1]["event"], "complete")
        self.assertEqual(log.steps[2]["event"], "compensate")
        self.assertEqual(log.steps[3]["event"], "compensated")

    def test_log_to_dict(self):
        log = SagaLog(saga_id="test-123")
        log.state = SagaState.COMPLETED
        log.record_step_start("s1")
        data = log.to_dict()
        self.assertEqual(data["sagaId"], "test-123")
        self.assertEqual(data["state"], "completed")
        self.assertEqual(len(data["steps"]), 1)

    def test_log_to_json(self):
        log = SagaLog(saga_id="test-123")
        log.record_step_start("s1")
        json_str = log.to_json()
        self.assertIn("test-123", json_str)
        self.assertIn("s1", json_str)


class SagaOrchestratorTests(unittest.TestCase):
    def test_start_and_get_saga(self):
        orch = SagaOrchestrator()
        saga = orch.start_saga("test-saga")
        self.assertIsInstance(saga, Saga)
        self.assertEqual(saga.name, "test-saga")

        retrieved = orch.get_saga(saga.saga_id)
        self.assertEqual(retrieved.saga_id, saga.saga_id)

    def test_get_nonexistent_saga(self):
        orch = SagaOrchestrator()
        self.assertIsNone(orch.get_saga("nonexistent"))

    def test_list_sagas(self):
        orch = SagaOrchestrator()
        s1 = orch.start_saga("s1")
        s2 = orch.start_saga("s2")
        sagas = orch.list_sagas()
        self.assertIn(s1.saga_id, sagas)
        self.assertIn(s2.saga_id, sagas)

    def test_get_saga_log(self):
        orch = SagaOrchestrator()
        saga = orch.start_saga("logged")
        saga.add_step("s1", lambda: 1)
        saga.execute()

        log = orch.get_saga_log(saga.saga_id)
        self.assertIsNotNone(log)
        self.assertEqual(log.saga_id, saga.saga_id)

    def test_custom_saga_id(self):
        orch = SagaOrchestrator()
        saga = orch.start_saga("custom", saga_id="my-id-123")
        self.assertEqual(saga.saga_id, "my-id-123")


class SagaChainingTests(unittest.TestCase):
    def test_add_step_chaining(self):
        saga = Saga("chain")
        result = saga.add_step("s1", lambda: 1)
        self.assertIs(result, saga)  # Returns self
        result = saga.add_step("s2", lambda: 2)
        self.assertIs(result, saga)
        results = saga.execute()
        self.assertEqual(results, [1, 2])


if __name__ == "__main__":
    unittest.main()
