"""Opt-in, loopback-only HTTP adapter for local AnyJev L0 decisions.

This is intentionally outside ``apexgraphswarm`` so importing the stdlib control
plane never imports AnyJev, vLLM, Transformers, or NumPy. The bridge starts only
when invoked as a separate process.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hmac
import ipaddress
import json
import math
import os
import re
import socket
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable, Mapping
from urllib.parse import urlsplit


DEFAULT_PORT = 8766
MAX_BODY_BYTES = 64 * 1024
MAX_STATE_CHARS = 16_000
MAX_QUESTIONS = 8
MAX_TOTAL_OPTIONS = 32
MAX_INSTRUCTIONS_CHARS = 2_000
MAX_LABEL_CHARS = 100
MAX_DESCRIPTION_CHARS = 500
MAX_INFERENCE_SECONDS = 35.0
MAX_HTTP_READ_SECONDS = 5.0
MAX_BACKEND_REQUEST_SECONDS = 8.0
SAFE_QUESTION_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,79}$")
LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}


class BridgeInputError(ValueError):
    """The request does not match the intentionally small bridge contract."""


def _reject_constant(value: str) -> None:
    raise BridgeInputError("JSON numbers must be finite.")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise BridgeInputError("JSON object keys must be unique.")
        result[key] = value
    return result


def _bounded_text(value: Any, name: str, maximum: int, *, empty: bool = False) -> str:
    if not isinstance(value, str) or len(value) > maximum or "\x00" in value:
        raise BridgeInputError(f"{name} must be text of at most {maximum} characters.")
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeEncodeError as exc:
        raise BridgeInputError(f"{name} must be valid Unicode text.") from exc
    if not empty and not value.strip():
        raise BridgeInputError(f"{name} must not be empty.")
    return value


def _labels_and_prompt(question_id: str, raw: Any, total_options: int) -> tuple[str, str, list[str], dict[str, str]]:
    if not isinstance(raw, dict) or set(raw) - {"type", "instructions", "criteria"}:
        raise BridgeInputError("Each question must contain only type, instructions, and criteria.")
    kind = raw.get("type")
    if kind not in {"choice", "score", "noul"}:
        raise BridgeInputError("Question type must be choice, score, or noul.")
    instructions = _bounded_text(raw.get("instructions"), "instructions", MAX_INSTRUCTIONS_CHARS)
    criteria = raw.get("criteria")
    labels: list[str] = []
    descriptions: dict[str, str] = {}

    if kind == "noul":
        if criteria is not None:
            raise BridgeInputError("noul questions do not accept criteria.")
        labels = ["Yes", "No"]
    elif isinstance(criteria, list):
        if not 2 <= len(criteria) <= (26 if kind == "choice" else 10):
            raise BridgeInputError("Choice criteria need 2–26 options; score criteria need 2–10 levels.")
        labels = [_bounded_text(item, "criterion", MAX_LABEL_CHARS) for item in criteria]
        descriptions = {label: "" for label in labels}
    elif isinstance(criteria, dict):
        if not 2 <= len(criteria) <= (26 if kind == "choice" else 10):
            raise BridgeInputError("Choice criteria need 2–26 options; score criteria need 2–10 levels.")
        for label, description in criteria.items():
            _bounded_text(label, "criterion label", MAX_LABEL_CHARS)
            _bounded_text(description, "criterion description", MAX_DESCRIPTION_CHARS, empty=True)
        labels = list(criteria)
        descriptions = dict(criteria)
    else:
        raise BridgeInputError("choice and score questions require a criteria list or label map.")

    if len(set(labels)) != len(labels):
        raise BridgeInputError("Question criteria labels must be unique.")
    total_options += len(labels)
    if total_options > MAX_TOTAL_OPTIONS:
        raise BridgeInputError(f"All questions together may contain at most {MAX_TOTAL_OPTIONS} decision options.")

    prompt = instructions
    if kind != "noul" and any(descriptions.values()):
        prompt += "\nUse these option meanings:\n" + "\n".join(
            f"- {label}: {description}" for label, description in descriptions.items() if description
        )
    return kind, prompt, labels, descriptions


def validate_payload(value: Any) -> dict[str, Any]:
    """Validate the bounded Laya-shaped request before constructing SDK objects."""
    if not isinstance(value, dict) or set(value) != {"state", "questions"}:
        raise BridgeInputError("Request must contain exactly state and questions.")
    state = _bounded_text(value["state"], "state", MAX_STATE_CHARS)
    questions = value["questions"]
    if not isinstance(questions, dict) or not 1 <= len(questions) <= MAX_QUESTIONS:
        raise BridgeInputError(f"questions must be an object with 1–{MAX_QUESTIONS} entries.")
    normalized = {}
    total_options = 0
    for question_id, raw in questions.items():
        if not isinstance(question_id, str) or not SAFE_QUESTION_ID.fullmatch(question_id):
            raise BridgeInputError("Question IDs must be short stable identifiers.")
        kind, prompt, labels, descriptions = _labels_and_prompt(question_id, raw, total_options)
        total_options += len(labels)
        normalized[question_id] = {
            "type": kind,
            "prompt": prompt,
            "labels": labels,
            "descriptions": descriptions,
        }
    return {"state": state, "questions": normalized}


def _finite_probability(value: Any) -> float:
    if isinstance(value, bool):
        raise ValueError("non-numeric probability")
    number = float(value)
    if not math.isfinite(number) or number < 0.0 or number > 1.0:
        raise ValueError("probability is outside [0, 1]")
    return number


def normalize_decisions(
    payload: dict[str, Any],
    decisions: Any,
    *,
    model: str,
) -> dict[str, Any]:
    """Copy only verified AnyJev decision fields into the stable bridge shape."""
    answers: dict[str, Any] = {}
    for question_id, question in payload["questions"].items():
        try:
            decision = decisions[question_id]
            distribution_raw = decision.distribution
            if not isinstance(distribution_raw, Mapping):
                raise ValueError("invalid distribution")
            labels = question["labels"]
            if set(distribution_raw) != set(labels):
                raise ValueError("distribution labels do not match request")
            distribution = {label: _finite_probability(distribution_raw[label]) for label in labels}
            if abs(sum(distribution.values()) - 1.0) > 1e-5:
                raise ValueError("distribution does not sum to one")
            confidence = _finite_probability(decision.confidence)
            if abs(confidence - max(distribution.values())) > 1e-5:
                raise ValueError("confidence does not match distribution")
            kind = question["type"]
            if kind == "noul":
                yes_probability = distribution.get("Yes")
                no_probability = distribution.get("No")
                if yes_probability is None or no_probability is None:
                    raise ValueError("invalid noul labels")
                # The application contract represents binary decisions as P(true),
                # independent of AnyJev's display answer threshold.
                result_value: str | float = yes_probability
                distribution = {"false": no_probability, "true": yes_probability}
            elif kind == "choice":
                answer = decision.answer
                if not isinstance(answer, str) or answer not in labels:
                    raise ValueError("invalid choice answer")
                result_value = answer
            else:
                answer = decision.value
                if isinstance(answer, bool) or not isinstance(answer, (int, float)) or not math.isfinite(float(answer)):
                    raise ValueError("invalid score answer")
                result_value = float(answer)
            answers[question_id] = {
                "type": kind,
                "value": result_value,
                "confidence": confidence,
                "distribution": distribution,
            }
        except Exception as exc:
            raise ValueError("AnyJev returned an invalid decision result.") from exc
    return {
        "model": model,
        "answers": answers,
        # AnyJev's Decision does not report token usage; preserve that as unknown.
        "usage": None,
        "routing": {"level": "L0"},
    }


def _local_http_origin(url: str, name: str) -> str:
    if not isinstance(url, str) or len(url) > 500:
        raise ValueError(f"{name} must be a local HTTP URL.")
    parsed = urlsplit(url)
    if parsed.scheme != "http" or parsed.hostname not in LOCAL_HOSTS or parsed.username or parsed.password:
        raise ValueError(f"{name} must use loopback HTTP without URL credentials.")
    if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
        raise ValueError(f"{name} must be a base origin without a path, query, or fragment.")
    return url.rstrip("/")


def create_anyjev_runtime(environment: Mapping[str, str]) -> tuple[Any, Callable[..., Any], str, str]:
    token = environment.get("ANYJEV_BRIDGE_TOKEN", "")
    if len(token) < 32:
        raise ValueError("ANYJEV_BRIDGE_TOKEN must contain at least 32 characters.")
    model = environment.get("ANYJEV_MODEL", "").strip()
    if not model or len(model) > 120 or "\x00" in model:
        raise ValueError("ANYJEV_MODEL must name the locally served model in at most 120 characters.")
    base_url = _local_http_origin(environment.get("ANYJEV_VLLM_URL", "http://127.0.0.1:8000"), "ANYJEV_VLLM_URL")
    try:
        from anyjev import Decider, Question
        from anyjev.backends.vllm import VLLMBackend
    except ImportError as exc:
        raise RuntimeError("Install AnyJev and its vLLM backend dependencies in the optional bridge environment.") from exc
    backend = VLLMBackend(base_url, model, workers=8, timeout=MAX_BACKEND_REQUEST_SECONDS)
    decider = Decider(backend, level="L0")
    return decider, Question, model, token


class BridgeService:
    def __init__(
        self,
        decider: Any,
        question_factory: Any,
        model: str,
        token: str,
        *,
        inference_timeout: float = MAX_INFERENCE_SECONDS,
    ) -> None:
        if len(token) < 32:
            raise ValueError("Bridge bearer token must contain at least 32 characters.")
        if not 0 < inference_timeout <= MAX_INFERENCE_SECONDS:
            raise ValueError("Inference timeout exceeds the supported limit.")
        self.decider = decider
        self.question_factory = question_factory
        self.model = model
        self.token = token
        self.inference_timeout = inference_timeout
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1, thread_name_prefix="anyjev-inference")
        self._slot = threading.Lock()

    def try_acquire(self) -> bool:
        return self._slot.acquire(blocking=False)

    def release(self) -> None:
        self._slot.release()

    def close(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)

    def decide(self, payload: dict[str, Any]) -> dict[str, Any]:
        questions = []
        for question_id, spec in payload["questions"].items():
            kind = spec["type"]
            if kind == "choice":
                question = self.question_factory.choice(spec["prompt"], spec["labels"], name=question_id)
            elif kind == "score":
                question = self.question_factory.score(spec["prompt"], levels=spec["labels"], name=question_id)
            else:
                question = self.question_factory.noul(spec["prompt"], name=question_id)
            questions.append(question)
        result = self.decider.decide(payload["state"], questions, level="L0")
        return normalize_decisions(payload, result, model=self.model)


def _is_loopback_address(value: str | None) -> bool:
    if not value:
        return False
    try:
        address = ipaddress.ip_address(value)
        if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped:
            address = address.ipv4_mapped
        return address.is_loopback
    except ValueError:
        return False


def _is_local_header_host(value: str | None) -> bool:
    if not value:
        return False
    parsed = urlsplit("//" + value)
    return parsed.hostname in LOCAL_HOSTS and parsed.username is None and parsed.password is None


def _origin_is_local(value: str | None) -> bool:
    if value is None:
        return True
    parsed = urlsplit(value)
    return parsed.scheme == "http" and parsed.hostname in LOCAL_HOSTS and parsed.username is None and parsed.password is None


def make_handler(service: BridgeService) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "AnyJevLocalBridge/1"
        sys_version = ""

        def setup(self) -> None:
            super().setup()
            self.connection.settimeout(MAX_HTTP_READ_SECONDS)

        def log_message(self, _format: str, *args: Any) -> None:
            return

        def _send(self, status: int, value: dict[str, Any]) -> None:
            try:
                encoded = json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")
            except (TypeError, ValueError):
                status, encoded = 500, b'{"error":"Bridge response could not be encoded."}'
            if len(encoded) > MAX_BODY_BYTES:
                status, encoded = 502, b'{"error":"Decision result exceeds the response limit."}'
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            try:
                self.wfile.write(encoded)
            except (BrokenPipeError, ConnectionResetError, OSError):
                pass

        def _local_peer(self) -> bool:
            return (
                _is_loopback_address(self.client_address[0])
                and _is_local_header_host(self.headers.get("Host"))
                and _origin_is_local(self.headers.get("Origin"))
            )

        def do_GET(self) -> None:
            if self.path != "/health" or not self._local_peer():
                self._send(404, {"error": "Not found."})
                return
            self._send(200, {"status": "ok", "provider": "anyjev", "model": service.model, "level": "L0"})

        def do_POST(self) -> None:
            if self.path != "/v1/systemone":
                self._send(404, {"error": "Not found."})
                return
            if not self._local_peer():
                self._send(403, {"error": "Loopback requests only."})
                return
            supplied = self.headers.get("Authorization", "")
            expected = "Bearer " + service.token
            if not hmac.compare_digest(supplied, expected):
                self._send(401, {"error": "Unauthorized."})
                return
            if not self.headers.get("Content-Type", "").lower().startswith("application/json"):
                self._send(415, {"error": "JSON content is required."})
                return
            try:
                length_raw = self.headers.get("Content-Length", "")
                if not length_raw.isascii() or not length_raw.isdecimal():
                    raise BridgeInputError("A valid Content-Length is required.")
                length = int(length_raw)
                if not 1 <= length <= MAX_BODY_BYTES:
                    self._send(413 if length > MAX_BODY_BYTES else 400, {"error": "Request body must be between 1 byte and 64 KiB."})
                    return
                deadline = time.monotonic() + MAX_HTTP_READ_SECONDS
                chunks = bytearray()
                while len(chunks) < length:
                    remaining_seconds = deadline - time.monotonic()
                    if remaining_seconds <= 0:
                        raise socket.timeout("request body deadline exceeded")
                    self.connection.settimeout(remaining_seconds)
                    chunk = self.rfile.read1(min(8192, length - len(chunks)))
                    if not chunk:
                        self._send(408, {"error": "Request body was incomplete."})
                        return
                    chunks.extend(chunk)
                self.connection.settimeout(MAX_HTTP_READ_SECONDS)
                raw = bytes(chunks)
                decoded = raw.decode("utf-8", errors="strict")
                value = json.loads(decoded, object_pairs_hook=_unique_object, parse_constant=_reject_constant)
                payload = validate_payload(value)
            except (BridgeInputError, UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
                message = str(exc) if isinstance(exc, BridgeInputError) else "Request body must be valid UTF-8 JSON."
                self._send(400, {"error": message[:200]})
                return
            except (TimeoutError, socket.timeout):
                self._send(408, {"error": "Request body read timed out."})
                return
            if not service.try_acquire():
                self._send(503, {"error": "The local decision worker is busy."})
                return
            try:
                future = service._executor.submit(service.decide, payload)
            except Exception:
                service.release()
                self._send(503, {"error": "The local decision worker is unavailable."})
                return
            future.add_done_callback(lambda _future: service.release())
            try:
                self._send(200, future.result(timeout=service.inference_timeout))
            except concurrent.futures.TimeoutError:
                # The underlying inference cannot be interrupted safely. The slot stays busy
                # until its completion callback runs, so timeout never creates overlap.
                self._send(504, {"error": "Decision timed out; the local inference is still draining."})
            except Exception:
                self._send(502, {"error": "The local decision provider failed."})

    return Handler


def serve(
    *,
    environment: Mapping[str, str] | None = None,
    port: int = DEFAULT_PORT,
    runtime_factory: Callable[[Mapping[str, str]], tuple[Any, Any, str, str]] = create_anyjev_runtime,
) -> None:
    env = os.environ if environment is None else environment
    host = env.get("ANYJEV_BRIDGE_HOST", "127.0.0.1")
    if host != "127.0.0.1":
        raise ValueError("ANYJEV_BRIDGE_HOST is fixed to 127.0.0.1.")
    decider, question_factory, model, token = runtime_factory(env)
    service = BridgeService(decider, question_factory, model, token)
    server = ThreadingHTTPServer(("127.0.0.1", port), make_handler(service))
    server.daemon_threads = True
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        service.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the optional loopback AnyJev L0 decision bridge.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args(argv)
    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")
    try:
        serve(port=args.port)
    except (ValueError, RuntimeError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
