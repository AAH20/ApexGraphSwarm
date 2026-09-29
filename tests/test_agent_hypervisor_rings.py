"""Tests for execution rings."""
import unittest

from kernels.agent_hypervisor.rings import (
    Ring, RingContext, RingError, RingPolicy, RingTransition,
    require_ring, transition_gate,
)


class RingEnumTests(unittest.TestCase):
    def test_ring_ordering(self):
        self.assertLess(Ring.KERNEL, Ring.SYSTEM)
        self.assertLess(Ring.SYSTEM, Ring.AGENT)
        self.assertLess(Ring.AGENT, Ring.USER)

    def test_ring_names(self):
        self.assertEqual(Ring.KERNEL.name, "kernel")
        self.assertEqual(Ring.SYSTEM.name, "system")
        self.assertEqual(Ring.AGENT.name, "agent")
        self.assertEqual(Ring.USER.name, "user")


class RingTransitionTests(unittest.TestCase):
    def test_valid_transition_to_more_privileged(self):
        t = RingTransition(source=Ring.USER, target=Ring.AGENT, gate="test")
        t.validate()  # Should not raise

    def test_invalid_transition_to_less_privileged(self):
        t = RingTransition(source=Ring.KERNEL, target=Ring.USER, gate="test")
        with self.assertRaises(RingError):
            t.validate()

    def test_invalid_transition_to_same_ring(self):
        t = RingTransition(source=Ring.AGENT, target=Ring.AGENT, gate="test")
        with self.assertRaises(RingError):
            t.validate()


class RingPolicyTests(unittest.TestCase):
    def test_default_transitions(self):
        policy = RingPolicy()
        self.assertTrue(policy.can_transition(Ring.USER, Ring.AGENT))
        self.assertTrue(policy.can_transition(Ring.USER, Ring.SYSTEM))
        self.assertTrue(policy.can_transition(Ring.USER, Ring.KERNEL))
        self.assertTrue(policy.can_transition(Ring.AGENT, Ring.SYSTEM))
        self.assertTrue(policy.can_transition(Ring.AGENT, Ring.KERNEL))
        self.assertTrue(policy.can_transition(Ring.SYSTEM, Ring.KERNEL))
        self.assertFalse(policy.can_transition(Ring.KERNEL, Ring.SYSTEM))
        self.assertFalse(policy.can_transition(Ring.SYSTEM, Ring.AGENT))
        self.assertFalse(policy.can_transition(Ring.AGENT, Ring.USER))

    def test_default_capabilities(self):
        policy = RingPolicy()
        self.assertTrue(policy.has_capability(Ring.KERNEL, "anything"))
        self.assertTrue(policy.has_capability(Ring.SYSTEM, "fs.read"))
        self.assertTrue(policy.has_capability(Ring.AGENT, "fs.read"))
        self.assertTrue(policy.has_capability(Ring.USER, "fs.read"))
        self.assertFalse(policy.has_capability(Ring.USER, "fs.write"))
        self.assertFalse(policy.has_capability(Ring.AGENT, "process.spawn"))

    def test_custom_policy(self):
        policy = RingPolicy(
            allowed_transitions={Ring.USER: {Ring.AGENT}},
            capabilities={Ring.AGENT: {"custom.cap"}},
        )
        self.assertTrue(policy.can_transition(Ring.USER, Ring.AGENT))
        self.assertFalse(policy.can_transition(Ring.USER, Ring.SYSTEM))
        self.assertTrue(policy.has_capability(Ring.AGENT, "custom.cap"))
        self.assertFalse(policy.has_capability(Ring.AGENT, "fs.read"))


class RingContextTests(unittest.TestCase):
    def test_default_is_kernel(self):
        RingContext.reset()
        self.assertEqual(RingContext.current(), Ring.KERNEL)

    def test_context_manager(self):
        RingContext.reset()
        self.assertEqual(RingContext.current(), Ring.KERNEL)
        with RingContext(Ring.AGENT):
            self.assertEqual(RingContext.current(), Ring.AGENT)
            with RingContext(Ring.USER):
                self.assertEqual(RingContext.current(), Ring.USER)
            self.assertEqual(RingContext.current(), Ring.AGENT)
        self.assertEqual(RingContext.current(), Ring.KERNEL)

    def test_context_manager_restores_on_exception(self):
        RingContext.reset()
        with self.assertRaises(ValueError):
            with RingContext(Ring.AGENT):
                raise ValueError("test")
        self.assertEqual(RingContext.current(), Ring.KERNEL)


class RequireRingTests(unittest.TestCase):
    def test_require_ring_allows_same_ring(self):
        RingContext.reset()
        with RingContext(Ring.AGENT):
            @require_ring(Ring.AGENT)
            def fn():
                return "ok"
            self.assertEqual(fn(), "ok")

    def test_require_ring_allows_more_privileged(self):
        RingContext.reset()
        with RingContext(Ring.KERNEL):
            @require_ring(Ring.AGENT)
            def fn():
                return "ok"
            self.assertEqual(fn(), "ok")

    def test_require_ring_rejects_less_privileged(self):
        RingContext.reset()
        with RingContext(Ring.USER):
            @require_ring(Ring.AGENT)
            def fn():
                return "ok"
            with self.assertRaises(RingError):
                fn()


class TransitionGateTests(unittest.TestCase):
    def test_valid_gate(self):
        gate = transition_gate(Ring.USER, Ring.AGENT, "test-gate")
        self.assertEqual(gate.source, Ring.USER)
        self.assertEqual(gate.target, Ring.AGENT)
        self.assertEqual(gate.gate, "test-gate")

    def test_invalid_gate_rejected_by_policy(self):
        policy = RingPolicy(allowed_transitions={Ring.USER: set()})
        with self.assertRaises(RingError):
            transition_gate(Ring.USER, Ring.AGENT, "test-gate", policy=policy)


if __name__ == "__main__":
    unittest.main()
