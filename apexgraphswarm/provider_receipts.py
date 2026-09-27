"""Provider usage normalization and non-billing vLLM allocation estimates.

Only metadata needed for accounting is returned. Provider payload text and
credentials are never copied into receipts or error messages.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_CEILING
import json
import math
import os
import re
import time
from typing import Any, Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

MICRO_USD = Decimal(1_000_000)
MAX_RECEIPT_BYTES = 256 * 1024
MAX_GENERATION_ID_LENGTH = 256
MAX_MODEL_LENGTH = 256
MAX_TOKEN_COUNT = 1_000_000_000
MAX_MICRO_USD = 2**63 - 1
MAX_GPU_COUNT = 128
MAX_ALLOCATION_SECONDS = 31 * 24 * 60 * 60
MAX_RATE_USD_PER_GPU_HOUR = Decimal("10000000")


class ReceiptError(ValueError):
    """Invalid, incomplete, or unreconciled provider receipt."""


def _text(value: Any, name: str, max_length: int = 256) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > max_length or "\x00" in value:
        raise ReceiptError("%s is missing or invalid" % name)
    return value.strip()


def _decimal(value: Any, name: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (Decimal, int, float, str)):
        raise ReceiptError("%s must be a numeric USD amount" % name)
    if isinstance(value, str) and (len(value) > 80 or not re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?", value)):
        raise ReceiptError("%s must be a finite USD amount" % name)
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ReceiptError("%s must be a finite USD amount" % name) from None
    if not amount.is_finite() or amount < 0:
        raise ReceiptError("%s must be a finite non-negative USD amount" % name)
    if amount > Decimal("1000000000000"):
        raise ReceiptError("%s exceeds the receipt limit" % name)
    return amount


def _count(value: Any, name: str) -> int:
    if type(value) is not int or value < 0 or value > MAX_TOKEN_COUNT:
        raise ReceiptError("%s must be a non-negative bounded integer" % name)
    return value


def _money(amount: Decimal) -> tuple[str, int]:
    micros = (amount * MICRO_USD).to_integral_value(rounding=ROUND_CEILING)
    if micros > MAX_MICRO_USD:
        raise ReceiptError("USD amount exceeds signed 64-bit micro-USD accounting range")
    return format(amount, "f"), int(micros)


def _json_size(payload: Mapping[str, Any]) -> int:
    try:
        data = json.dumps(payload, ensure_ascii=False, separators=(",", ":"),
                          allow_nan=False, default=lambda value: str(value)).encode("utf-8")
    except (TypeError, ValueError, UnicodeError):
        raise ReceiptError("provider payload is not bounded JSON metadata") from None
    if len(data) > MAX_RECEIPT_BYTES:
        raise ReceiptError("provider metadata exceeds the receipt size limit")
    return len(data)


def _consistent_optional(values: list[Any], field: str) -> Any:
    present = [value for value in values if value is not None]
    if not present:
        return None
    if any(value != present[0] for value in present[1:]):
        raise ReceiptError("provider returned conflicting %s values" % field)
    return present[0]


def normalize_openrouter_receipt(
    payload: Mapping[str, Any],
    expected_generation_id: str,
    expected_model: str | None = None,
) -> dict[str, Any]:
    """Normalize one OpenRouter completion or generation-metadata response.

    `expected_generation_id` is obtained from the original response's generation
    id/header or a caller's persisted request record. It is a reconciliation key,
    not cryptographic proof of origin. No unknown cost is converted to zero.
    """
    expected_id = _text(expected_generation_id, "expected_generation_id", MAX_GENERATION_ID_LENGTH)
    if not isinstance(payload, Mapping) or len(payload) > 96:
        raise ReceiptError("provider payload must be a bounded object")
    _json_size(payload)
    data = payload.get("data")
    if data is not None and not isinstance(data, Mapping):
        raise ReceiptError("generation metadata data field must be an object")
    data_obj: Mapping[str, Any] = data if isinstance(data, Mapping) else {}
    usage = payload.get("usage")
    if usage is not None and not isinstance(usage, Mapping):
        raise ReceiptError("completion usage must be an object")
    usage_obj: Mapping[str, Any] = usage if isinstance(usage, Mapping) else {}

    generation_ids: list[Any] = []
    for key in ("generation_id", "generationId", "x-generation-id", "X-Generation-Id"):
        if payload.get(key) is not None:
            generation_ids.append(payload[key])
    if data_obj.get("id") is not None:
        generation_ids.append(data_obj["id"])
    top_id = payload.get("id")
    if isinstance(top_id, str) and (top_id == expected_id or top_id.startswith("gen-")):
        generation_ids.append(top_id)
    normalized_ids = [_text(value, "generation ID", MAX_GENERATION_ID_LENGTH) for value in generation_ids]
    if not normalized_ids or any(value != expected_id for value in normalized_ids):
        raise ReceiptError("OpenRouter generation ID is missing or does not match the expected ID")

    response_id_raw = top_id if top_id is not None and top_id != expected_id else None
    response_id = _text(response_id_raw, "response ID", MAX_GENERATION_ID_LENGTH) if response_id_raw is not None else None
    model = _consistent_optional([payload.get("model"), data_obj.get("model")], "model")
    model = _text(model, "returned model", MAX_MODEL_LENGTH)
    requested_model = _text(expected_model, "expected_model", MAX_MODEL_LENGTH) if expected_model is not None else None
    if requested_model is not None and model != requested_model:
        raise ReceiptError("OpenRouter returned model does not match the expected model")

    currency_values = [payload.get("currency"), data_obj.get("currency"), usage_obj.get("currency")]
    currency = _consistent_optional(currency_values, "currency")
    if currency is not None and currency != "USD":
        raise ReceiptError("OpenRouter cost currency is not USD")

    cost_candidates: list[tuple[str, Decimal]] = []
    if usage_obj.get("cost") is not None:
        cost_candidates.append(("usage.cost", _decimal(usage_obj["cost"], "usage.cost")))
    if data_obj.get("total_cost") is not None:
        cost_candidates.append(("data.total_cost", _decimal(data_obj["total_cost"], "data.total_cost")))
    # Generation-history data also exposes `usage` as the billed USD amount.
    if isinstance(data_obj.get("usage"), (Decimal, int, float)) and not isinstance(data_obj.get("usage"), bool):
        cost_candidates.append(("data.usage", _decimal(data_obj["usage"], "data.usage")))
    if not data_obj and payload.get("total_cost") is not None:
        cost_candidates.append(("total_cost", _decimal(payload["total_cost"], "total_cost")))
    if not cost_candidates:
        raise ReceiptError("OpenRouter actual USD cost is unavailable; leave accounting unresolved")
    cost = cost_candidates[0][1]
    if any(candidate_cost != cost for _, candidate_cost in cost_candidates[1:]):
        raise ReceiptError("OpenRouter returned conflicting cost fields")
    cost_source = "+".join(source for source, _ in cost_candidates)
    cost_usd, cost_microusd = _money(cost)

    prompt_values = [usage_obj.get("prompt_tokens"), data_obj.get("tokens_prompt")]
    completion_values = [usage_obj.get("completion_tokens"), data_obj.get("tokens_completion")]
    prompt = _consistent_optional(prompt_values, "prompt token count")
    completion = _consistent_optional(completion_values, "completion token count")
    if prompt is not None:
        prompt = _count(prompt, "prompt_tokens")
    if completion is not None:
        completion = _count(completion, "completion_tokens")
    total = _consistent_optional([usage_obj.get("total_tokens")], "total token count")
    if total is not None:
        total = _count(total, "total_tokens")
    if total is None and prompt is not None and completion is not None:
        total = prompt + completion
    elif total is not None and prompt is not None and completion is not None and total != prompt + completion:
        raise ReceiptError("OpenRouter token totals do not reconcile")
    reasoning = usage_obj.get("completion_tokens_details", {}).get("reasoning_tokens") if isinstance(usage_obj.get("completion_tokens_details"), Mapping) else data_obj.get("native_tokens_reasoning")
    cached = usage_obj.get("prompt_tokens_details", {}).get("cached_tokens") if isinstance(usage_obj.get("prompt_tokens_details"), Mapping) else data_obj.get("native_tokens_cached")
    if reasoning is not None:
        reasoning = _count(reasoning, "reasoning_tokens")
    if cached is not None:
        cached = _count(cached, "cached_tokens")

    provider_name = data_obj.get("provider_name")
    if provider_name is not None:
        provider_name = _text(provider_name, "provider_name", 128)
    return {
        "provider": "openrouter", "receiptType": "generation_metadata" if data_obj else "completion_response",
        "generationId": expected_id, "responseId": response_id, "model": model,
        "requestedModel": requested_model, "providerName": provider_name,
        "currency": "USD", "costUsd": cost_usd, "costMicrousd": cost_microusd,
        "costRounding": "ROUND_CEILING", "costSource": cost_source,
        "tokenUsage": {"prompt": prompt, "completion": completion, "total": total,
                       "reasoning": reasoning, "cachedPrompt": cached},
        "reconciliation": "expected-generation-id-match",
    }


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _fetch_generation_bytes(url: str, headers: Mapping[str, str], timeout_seconds: float,
                            max_response_bytes: int) -> bytes:
    request = Request(url, headers=dict(headers), method="GET")
    opener = build_opener(_NoRedirect())
    started = time.monotonic()
    try:
        with opener.open(request, timeout=timeout_seconds) as response:
            if response.status != 200:
                raise ReceiptError("OpenRouter generation lookup returned HTTP %d" % response.status)
            content_length = response.headers.get("Content-Length")
            if content_length is not None:
                try:
                    if int(content_length) > max_response_bytes:
                        raise ReceiptError("OpenRouter generation response exceeds size limit")
                except ValueError:
                    raise ReceiptError("OpenRouter generation response has invalid length") from None
            chunks = bytearray()
            while True:
                if time.monotonic() - started > timeout_seconds:
                    raise ReceiptError("OpenRouter generation lookup exceeded its deadline")
                chunk = response.read(min(16_384, max_response_bytes + 1 - len(chunks)))
                if not chunk:
                    break
                chunks.extend(chunk)
                if len(chunks) > max_response_bytes:
                    raise ReceiptError("OpenRouter generation response exceeds size limit")
            return bytes(chunks)
    except HTTPError as exc:
        if 300 <= exc.code < 400:
            raise ReceiptError("OpenRouter generation lookup redirects are not allowed") from None
        raise ReceiptError("OpenRouter generation lookup failed with HTTP %d" % exc.code) from None
    except (URLError, TimeoutError, OSError) as exc:
        raise ReceiptError("OpenRouter generation lookup failed (%s)" % type(exc).__name__) from None


def reconcile_openrouter_generation(
    expected_generation_id: str,
    expected_model: str | None = None,
    *,
    api_key: str | None = None,
    timeout_seconds: float = 5.0,
    max_response_bytes: int = 256 * 1024,
    fetcher: Callable[[str, Mapping[str, str], float, int], bytes] | None = None,
) -> dict[str, Any]:
    """Fetch metadata for an existing generation ID from the fixed OpenRouter host.

    `fetcher` is an injection seam receiving that exact URL for tests; production
    cannot configure another destination. This lookup does not create a model run.
    """
    generation_id = _text(expected_generation_id, "expected_generation_id", MAX_GENERATION_ID_LENGTH)
    key = api_key if api_key is not None else os.environ.get("OPENROUTER_API_KEY")
    key = _text(key, "OPENROUTER_API_KEY", 4096)
    if "\r" in key or "\n" in key:
        raise ReceiptError("OPENROUTER_API_KEY is invalid")
    if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)) or not math.isfinite(timeout_seconds) or not 0.1 <= timeout_seconds <= 10:
        raise ReceiptError("timeout_seconds must be between 0.1 and 10 seconds")
    if type(max_response_bytes) is not int or not 1 <= max_response_bytes <= MAX_RECEIPT_BYTES:
        raise ReceiptError("max_response_bytes is outside the allowed range")
    url = "https://openrouter.ai/api/v1/generation?" + urlencode({"id": generation_id})
    headers = {"Authorization": "Bearer " + key, "Accept": "application/json"}
    try:
        body = (fetcher or _fetch_generation_bytes)(url, headers, float(timeout_seconds), max_response_bytes)
    except ReceiptError:
        raise
    except Exception as exc:
        raise ReceiptError("OpenRouter generation lookup failed (%s)" % type(exc).__name__) from None
    if not isinstance(body, bytes) or len(body) > max_response_bytes:
        raise ReceiptError("OpenRouter generation response exceeds size limit")
    try:
        payload = json.loads(body.decode("utf-8"), parse_float=Decimal,
                             parse_constant=lambda _: (_ for _ in ()).throw(ValueError("non-finite")))
    except (UnicodeError, json.JSONDecodeError, ValueError):
        raise ReceiptError("OpenRouter generation response is not valid finite JSON") from None
    return normalize_openrouter_receipt(payload, generation_id, expected_model)


def _round_micro_usd(amount_usd: Decimal) -> int:
    micros = (amount_usd * MICRO_USD).to_integral_value(rounding=ROUND_CEILING)
    if micros > MAX_MICRO_USD:
        raise ReceiptError("estimate exceeds signed 64-bit micro-USD range")
    return int(micros)


def estimate_vllm_allocation_cost(
    *, gpu_count: int, gpu_hourly_rate_usd: Any, allocated_seconds: Any,
    allocation_mode: str, shared_fraction: Any = None,
    amortized_gpu_hourly_rate_usd: Any = None,
) -> dict[str, Any]:
    """Return vLLM GPU-time cost estimates; these are never provider billing."""
    if type(gpu_count) is not int or not 1 <= gpu_count <= MAX_GPU_COUNT:
        raise ReceiptError("gpu_count must be an integer from 1 to %d" % MAX_GPU_COUNT)
    if allocation_mode not in ("exclusive", "shared"):
        raise ReceiptError("allocation_mode must be exclusive or shared")
    seconds = _decimal(allocated_seconds, "allocated_seconds")
    if seconds > MAX_ALLOCATION_SECONDS:
        raise ReceiptError("allocated_seconds exceeds the allocation limit")
    rate = None if gpu_hourly_rate_usd is None else _decimal(gpu_hourly_rate_usd, "gpu_hourly_rate_usd")
    amortized_rate = None if amortized_gpu_hourly_rate_usd is None else _decimal(amortized_gpu_hourly_rate_usd, "amortized_gpu_hourly_rate_usd")
    for amount, label in ((rate, "gpu_hourly_rate_usd"), (amortized_rate, "amortized_gpu_hourly_rate_usd")):
        if amount is not None and amount > MAX_RATE_USD_PER_GPU_HOUR:
            raise ReceiptError("%s exceeds the estimate limit" % label)
    share = None if shared_fraction is None else _decimal(shared_fraction, "shared_fraction")
    if allocation_mode == "exclusive" and share is not None:
        raise ReceiptError("shared_fraction is only valid for shared allocation")
    if allocation_mode == "shared" and share is not None and not Decimal(0) < share <= Decimal(1):
        raise ReceiptError("shared_fraction must be greater than 0 and at most 1")
    if allocation_mode == "exclusive":
        share = Decimal(1)

    full_compute = Decimal(gpu_count) * rate * seconds / Decimal(3600) if rate is not None else None
    full_amortized = Decimal(gpu_count) * amortized_rate * seconds / Decimal(3600) if amortized_rate is not None else None
    attributed_compute = full_compute * share if full_compute is not None and share is not None else None
    attributed_amortized = full_amortized * share if full_amortized is not None and share is not None else None
    full_compute_usd, full_compute_micro = (None, None) if full_compute is None else (format(full_compute, "f"), _round_micro_usd(full_compute))
    full_amortized_usd, full_amortized_micro = (None, None) if full_amortized is None else (format(full_amortized, "f"), _round_micro_usd(full_amortized))
    attributed_compute_usd, attributed_compute_micro = (None, None) if attributed_compute is None else (format(attributed_compute, "f"), _round_micro_usd(attributed_compute))
    attributed_amortized_usd, attributed_amortized_micro = (None, None) if attributed_amortized is None else (format(attributed_amortized, "f"), _round_micro_usd(attributed_amortized))
    attributed_total = (attributed_compute_micro + attributed_amortized_micro
                        if attributed_compute_micro is not None and attributed_amortized_micro is not None else None)
    return {
        "provider": "vllm", "billingStatus": "not_billing", "estimateOnly": True,
        "allocationMode": allocation_mode, "gpuCount": gpu_count,
        "allocatedSeconds": format(seconds, "f"),
        "gpuHourlyRateUsd": None if rate is None else format(rate, "f"),
        "sharedFraction": None if allocation_mode == "exclusive" or shared_fraction is None else format(share, "f"),
        "fullPoolComputeEstimateUsd": full_compute_usd,
        "fullPoolComputeEstimateMicrousd": full_compute_micro,
        "attributedComputeEstimateUsd": attributed_compute_usd,
        "attributedComputeEstimateMicrousd": attributed_compute_micro,
        "amortizedGpuHourlyRateUsd": None if amortized_rate is None else format(amortized_rate, "f"),
        "fullPoolAmortizedEstimateUsd": full_amortized_usd,
        "fullPoolAmortizedEstimateMicrousd": full_amortized_micro,
        "attributedAmortizedEstimateUsd": attributed_amortized_usd,
        "attributedAmortizedEstimateMicrousd": attributed_amortized_micro,
        "attributedTotalEstimateMicrousd": attributed_total,
        "rounding": "ROUND_CEILING",
        "uncertainty": ("shared GPU-time cost cannot be attributed without shared_fraction"
                        if allocation_mode == "shared" and shared_fraction is None
                        else "caller-supplied rates and allocation inputs; not an invoice or measured per-request power draw"),
    }


def cli_dispatch(payload: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, Mapping) or len(payload) > 16:
        raise ReceiptError("request must be a bounded object")
    action = payload.get("action")
    if action == "normalizeOpenRouter":
        allowed = {"action", "payload", "expectedGenerationId", "expectedModel"}
        if set(payload) - allowed:
            raise ReceiptError("request contains unsupported fields")
        return normalize_openrouter_receipt(payload.get("payload"), payload.get("expectedGenerationId"), payload.get("expectedModel"))
    if action == "fetchOpenRouterGeneration":
        allowed = {"action", "expectedGenerationId", "expectedModel"}
        if set(payload) - allowed:
            raise ReceiptError("request contains unsupported fields")
        return reconcile_openrouter_generation(payload.get("expectedGenerationId"), payload.get("expectedModel"))
    if action == "estimateVllmAllocation":
        allowed = {"action", "gpuCount", "gpuHourlyRateUsd", "allocatedSeconds", "allocationMode", "sharedFraction", "amortizedGpuHourlyRateUsd"}
        if set(payload) - allowed:
            raise ReceiptError("request contains unsupported fields")
        return estimate_vllm_allocation_cost(
            gpu_count=payload.get("gpuCount"), gpu_hourly_rate_usd=payload.get("gpuHourlyRateUsd"),
            allocated_seconds=payload.get("allocatedSeconds"), allocation_mode=payload.get("allocationMode"),
            shared_fraction=payload.get("sharedFraction"),
            amortized_gpu_hourly_rate_usd=payload.get("amortizedGpuHourlyRateUsd"),
        )
    raise ReceiptError("unsupported receipt action")


def main() -> int:
    import sys
    raw = sys.stdin.buffer.read(MAX_RECEIPT_BYTES + 1)
    if len(raw) > MAX_RECEIPT_BYTES:
        result = {"error": "input exceeds receipt request size limit"}
        code = 2
    else:
        try:
            request = json.loads(raw.decode("utf-8"), parse_float=Decimal,
                                 parse_constant=lambda _: (_ for _ in ()).throw(ValueError("non-finite")))
            result, code = cli_dispatch(request), 0
        except (UnicodeError, json.JSONDecodeError, ValueError, TypeError) as exc:
            result, code = {"error": str(exc) if isinstance(exc, ReceiptError) else "invalid receipt request"}, 2
    sys.stdout.write(json.dumps(result, separators=(",", ":"), allow_nan=False) + "\n")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
