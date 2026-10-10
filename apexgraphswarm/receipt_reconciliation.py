"""Operator-assisted reconciliation for OpenRouter-backed task attempts.

This module binds supplied provider metadata to generation/model identities that
were persisted before and after each invocation. It does not contact OpenRouter;
the caller supplies trusted local operator assertions for reconciliation.
"""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from typing import Any, Mapping

from .control import ControlError, ControlStore, MAX_ATTEMPTS, MAX_CHECKPOINTS_PER_ATTEMPT
from .provider_receipts import ReceiptError, normalize_openrouter_receipt

MAX_INPUT_BYTES = 2 * 1024 * 1024
MAX_OPERATOR_ID = 128
OPENROUTER_TOOLS = {"integration:openrouter:review", "integration:openrouter:delegate"}


def _identifier(value: Any, label: str, maximum: int = 256) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum or "\x00" in value:
        raise ControlError(f"{label} is missing or invalid.")
    return value.strip()


def _saved_call_map(context: Mapping[str, Any]) -> tuple[dict[tuple[int, str], dict[str, Any]], dict[tuple[int, str], dict[str, Any]]]:
    starts: dict[tuple[int, str], dict[str, Any]] = {}
    responses: dict[tuple[int, str], dict[str, Any]] = {}
    checkpoints = context.get("checkpoints")
    if not isinstance(checkpoints, list) or len(checkpoints) > MAX_ATTEMPTS * MAX_CHECKPOINTS_PER_ATTEMPT:
        raise ControlError("Saved provider checkpoints are missing or exceed limits.")
    for row in checkpoints:
        if not isinstance(row, dict) or set(row) != {"attempt", "checkpointId", "value"}:
            raise ControlError("Saved provider checkpoint has an invalid shape.")
        attempt = row["attempt"]
        if type(attempt) is not int or not 1 <= attempt <= MAX_ATTEMPTS:
            raise ControlError("Saved provider checkpoint attempt is invalid.")
        checkpoint_id = row["checkpointId"]
        value = row["value"]
        if not isinstance(checkpoint_id, str) or not isinstance(value, dict):
            raise ControlError("Saved provider checkpoint identity is invalid.")
        call_id = _identifier(value.get("callId"), "saved callId")
        if checkpoint_id == call_id + ":started":
            target = starts
        elif checkpoint_id == call_id + ":receipt":
            target = responses
        else:
            raise ControlError("Saved provider checkpoint ID does not match its call identity.")
        key = (attempt, call_id)
        if key in target:
            raise ControlError("Saved provider checkpoints contain duplicate call identities.")
        target[key] = value
    return starts, responses


def reconcile_openrouter_task(
    store: ControlStore,
    task_id: str,
    entries: list[dict[str, Any]],
    *,
    operator_id: str,
) -> dict[str, Any]:
    """Reconcile every recorded OpenRouter call for one unresolved task.

    Each entry is ``{"attempt": int, "callId": str, "payload": {...}}``.
    Coverage must exactly equal saved ``:started`` checkpoints across all
    attempts. Each payload is normalized against the saved generation ID and
    model before an atomic settlement is requested from ``ControlStore``.
    """
    task_id = _identifier(task_id, "task_id")
    operator_id = _identifier(operator_id, "operator_id", MAX_OPERATOR_ID)
    if not isinstance(entries, list) or not entries or len(entries) > MAX_ATTEMPTS * MAX_CHECKPOINTS_PER_ATTEMPT:
        raise ControlError("Receipt entries must be a bounded non-empty list.")
    try:
        encoded = json.dumps(entries, ensure_ascii=False, separators=(",", ":"),
                             allow_nan=False, default=str)
    except (TypeError, ValueError, RecursionError, UnicodeError):
        raise ControlError("Receipt entries must be finite JSON metadata.") from None
    if len(encoded.encode("utf-8")) > MAX_INPUT_BYTES:
        raise ControlError("Receipt entries exceed the reconciliation size limit.")

    context = store.provider_receipt_context(task_id)
    prior_audit = store.receipt_reconciliation(task_id)
    if context.get("status") != "needs_reconciliation" and prior_audit is None:
        raise ControlError("Task is not awaiting cost reconciliation.")
    if context.get("tool") not in OPENROUTER_TOOLS:
        raise ControlError("Task is not an OpenRouter review/delegation task.")
    starts, responses = _saved_call_map(context)
    if not starts or set(starts) != set(responses):
        raise ControlError("Every saved OpenRouter call needs a response checkpoint before reconciliation.")

    supplied: dict[tuple[int, str], Any] = {}
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {"attempt", "callId", "payload"}:
            raise ControlError("Each entry must contain only attempt, callId, and payload.")
        attempt = entry["attempt"]
        if type(attempt) is not int or not 1 <= attempt <= MAX_ATTEMPTS:
            raise ControlError("Entry attempt number is invalid.")
        call_id = _identifier(entry["callId"], "callId")
        key = (attempt, call_id)
        if key in supplied:
            raise ControlError("Duplicate OpenRouter receipt entry.")
        supplied[key] = entry["payload"]
    if set(supplied) != set(starts):
        raise ControlError("Receipt entries must cover every saved started call exactly once.")

    normalized_entries = []
    for key in sorted(starts):
        start = starts[key]
        response = responses[key]
        if start.get("provider") != "openrouter" or response.get("provider") != "openrouter":
            raise ControlError("Saved call checkpoints do not identify OpenRouter.")
        expected_model = _identifier(start.get("model"), "saved request model", 256)
        response_model = _identifier(response.get("model"), "saved returned model", 256)
        if expected_model != response_model:
            raise ControlError("Saved request and response model IDs do not match.")
        expected_generation_id = _identifier(response.get("generationId"), "saved generation ID", 256)
        # Never infer a generation identity from caller-supplied payload data.
        try:
            receipt = normalize_openrouter_receipt(
                supplied[key], expected_generation_id=expected_generation_id,
                expected_model=expected_model,
            )
        except ReceiptError as exc:
            raise ControlError(f"OpenRouter receipt rejected: {exc}") from None
        normalized_entries.append({"attempt": key[0], "callId": key[1], "receipt": receipt})

    # The store re-reads checkpoints and attempt rows while holding its write
    # transaction, closing the gap between this preflight and atomic settlement.
    return store.reconcile_provider_receipts(task_id, normalized_entries, operator_id=operator_id)


def _cli() -> int:
    raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    if len(raw) > MAX_INPUT_BYTES:
        print(json.dumps({"ok": False, "error": "input exceeds the reconciliation size limit"}))
        return 2
    try:
        request = json.loads(raw.decode("utf-8"), parse_float=Decimal,
                             parse_constant=lambda _: (_ for _ in ()).throw(ValueError("invalid number")))
        if not isinstance(request, dict) or set(request) != {"action", "dbPath", "taskId", "operatorId", "receipts"}:
            raise ControlError("Request must contain action, dbPath, taskId, operatorId, and receipts.")
        if request["action"] != "reconcileOpenRouterReceipts":
            raise ControlError("Unsupported receipt reconciliation action.")
        db_path = _identifier(request["dbPath"], "dbPath", 4096)
        with ControlStore(db_path) as store:
            result = reconcile_openrouter_task(store, request["taskId"], request["receipts"],
                                               operator_id=request["operatorId"])
        print(json.dumps({"ok": True, "data": result}, ensure_ascii=False, separators=(",", ":")))
        return 0
    except (ControlError, ValueError, UnicodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, separators=(",", ":")))
        return 1


if __name__ == "__main__":
    raise SystemExit(_cli())
