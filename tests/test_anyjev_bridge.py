from __future__ import annotations

import http.client
import json
import threading
import time
import unittest
from dataclasses import dataclass
from http.server import ThreadingHTTPServer
from typing import Any

from integrations.anyjev_bridge import (
    BridgeService,
    make_handler,
    normalize_decisions,
    validate_payload,
)


TOKEN = "test-only-loopback-secret-with-more-than-32-characters"


@dataclass
class FakeQuestion:
    kind: str
    text: str
    options: list[str]
    name: str


class FakeQuestionFactory:
    @staticmethod
    def choice(text: str, options: list[str], *, name: str) -> FakeQuestion:
        return FakeQuestion("choice", text, list(options), name)

    @staticmethod
    def score(text: str, *, levels: list[str], name: str) -> FakeQuestion:
        return FakeQuestion("score", text, list(levels), name)

    @staticmethod
    def noul(text: str, *, name: str) -> FakeQuestion:
        return FakeQuestion("noul", text, ["Yes", "No"], name)


class FakeDecision:
    def __init__(self, question: FakeQuestion) -> None:
        self.distribution = {label: (0.8 if index == 0 else 0.2 / (len(question.options) - 1))
                             for index, label in enumerate(question.options)}
        self.confidence = max(self.distribution.values())
        self.answer = (question.options[0] == "Yes") if question.kind == "noul" else question.options[0]
        self.value = 0.75


class FakeDecider:
    def __init__(self) -> None:
        self.called = threading.Event()
        self.release_call = threading.Event()
        self.questions: list[FakeQuestion] = []
        self.state: Any = None
        self.fail = False

    def decide(self, state: str, questions: list[FakeQuestion], *, level: str) -> dict[str, FakeDecision]:
        self.state = state
        self.questions = questions
        self.called.set()
        self.release_call.wait(2)
        if self.fail:
            raise RuntimeError("fake upstream error contains a secret")
        if level != "L0":
            raise AssertionError("bridge must use L0")
        return {question.name: FakeDecision(question) for question in questions}


class AnyJevBridgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.decider = FakeDecider()
        self.service = BridgeService(self.decider, FakeQuestionFactory, "fixture-model", TOKEN, inference_timeout=0.5)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(self.service))
        self.server.daemon_threads = True
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.server.server_address[1]

    def tearDown(self) -> None:
        self.decider.release_call.set()
        self.server.shutdown()
        self.server.server_close()
        self.service.close()
        self.thread.join(timeout=2)

    @staticmethod
    def valid_payload() -> dict[str, Any]:
        return {
            "state": "A user reports two charges for one order.",
            "questions": {
                "route": {"type": "choice", "instructions": "Choose a support team.",
                          "criteria": {"billing": "Refund and payment issues", "technical": "Product defects"}},
                "urgent": {"type": "noul", "instructions": "Does this require immediate escalation?"},
                "severity": {"type": "score", "instructions": "Rate severity.", "criteria": ["low", "medium", "high"]},
            },
        }

    def post(self, value: Any, *, token: str | None = TOKEN, origin: str | None = None) -> tuple[int, dict[str, Any]]:
        body = value if isinstance(value, bytes) else json.dumps(value).encode("utf-8")
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=3)
        headers = {"Content-Type": "application/json", "Content-Length": str(len(body))}
        if token is not None:
            headers["Authorization"] = f"Bearer {token}"
        if origin is not None:
            headers["Origin"] = origin
        connection.request("POST", "/v1/systemone", body=body, headers=headers)
        response = connection.getresponse()
        payload = json.loads(response.read())
        connection.close()
        return response.status, payload

    def test_laya_shape_returns_normalized_l0_answers_and_unknown_usage(self) -> None:
        self.decider.release_call.set()
        status, result = self.post(self.valid_payload())
        self.assertEqual(status, 200)
        self.assertEqual(result["model"], "fixture-model")
        self.assertEqual(result["routing"], {"level": "L0"})
        self.assertIsNone(result["usage"])
        self.assertEqual(set(result["answers"]), {"route", "urgent", "severity"})
        self.assertEqual(result["answers"]["route"]["type"], "choice")
        self.assertEqual(result["answers"]["route"]["value"], "billing")
        self.assertAlmostEqual(sum(result["answers"]["route"]["distribution"].values()), 1.0)
        self.assertEqual(result["answers"]["urgent"]["value"], 0.8)
        self.assertEqual(result["answers"]["urgent"]["distribution"], {"false": 0.2, "true": 0.8})
        self.assertEqual(result["answers"]["severity"]["value"], 0.75)
        self.assertEqual(len(self.decider.questions), 3)
        self.assertIn("Refund and payment issues", self.decider.questions[0].text)

    def test_authentication_and_nonlocal_origin_are_rejected(self) -> None:
        body = self.valid_payload()
        self.assertEqual(self.post(body, token="wrong")[0], 401)
        self.assertEqual(self.post(body, origin="https://attacker.example")[0], 403)

    def test_request_size_and_shape_limits_are_enforced(self) -> None:
        self.assertEqual(self.post(b" " * (64 * 1024 + 1))[0], 413)
        too_many = {"state": "s", "questions": {f"q{i}": {"type": "noul", "instructions": "ok"} for i in range(9)}}
        status, body = self.post(too_many)
        self.assertEqual(status, 400)
        self.assertIn("1–8", body["error"])

    def test_question_validation_bounds_llm_fanout_and_rejects_extra_fields(self) -> None:
        body = self.valid_payload()
        body["questions"]["route"]["criteria"] = {f"option-{i}": "meaning" for i in range(26)}
        body["questions"]["severity"]["criteria"] = [f"level-{i}" for i in range(10)]
        with self.assertRaisesRegex(ValueError, "at most 32"):
            validate_payload(body)
        body = self.valid_payload()
        body["providerUrl"] = "http://attacker.invalid"
        with self.assertRaisesRegex(ValueError, "exactly state and questions"):
            validate_payload(body)

    def test_upstream_errors_are_generic_and_do_not_echo_exception(self) -> None:
        self.decider.fail = True
        self.decider.release_call.set()
        status, body = self.post(self.valid_payload())
        self.assertEqual(status, 502)
        self.assertEqual(body, {"error": "The local decision provider failed."})

    def test_timeout_keeps_serialized_slot_until_underlying_inference_drains(self) -> None:
        self.service.inference_timeout = 0.05
        first: list[tuple[int, dict[str, Any]]] = []
        first_thread = threading.Thread(target=lambda: first.append(self.post(self.valid_payload())))
        first_thread.start()
        self.assertTrue(self.decider.called.wait(1))
        first_thread.join(timeout=1)
        self.assertFalse(first_thread.is_alive())
        self.assertEqual(first[0][0], 504)
        status, body = self.post(self.valid_payload())
        self.assertEqual(status, 503)
        self.assertIn("busy", body["error"])
        self.decider.release_call.set()
        deadline = time.monotonic() + 1
        while self.service._slot.locked() and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertFalse(self.service._slot.locked())

    def test_normalizer_rejects_invalid_probability_payload(self) -> None:
        payload = validate_payload({"state": "s", "questions": {"route": {
            "type": "choice", "instructions": "choose", "criteria": ["a", "b"]}}})

        class Invalid:
            distribution = {"a": float("nan"), "b": 0.0}
            confidence = 1.0
            answer = "a"

        with self.assertRaisesRegex(ValueError, "invalid decision"):
            normalize_decisions(payload, {"route": Invalid()}, model="fixture")


if __name__ == "__main__":
    unittest.main()
