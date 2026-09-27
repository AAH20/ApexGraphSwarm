import json
import unittest
from decimal import Decimal
from urllib.parse import parse_qs, urlsplit

from apexgraphswarm.provider_receipts import (
    ReceiptError,
    cli_dispatch,
    estimate_vllm_allocation_cost,
    normalize_openrouter_receipt,
    reconcile_openrouter_generation,
)


class OpenRouterReceiptTests(unittest.TestCase):
    def test_normalizes_completion_and_ceil_micro_usd(self):
        receipt = normalize_openrouter_receipt({
            "id": "gen-abc", "model": "vendor/model-v2",
            "usage": {"prompt_tokens": 11, "completion_tokens": 7,
                      "total_tokens": 18, "cost": "0.0000004",
                      "completion_tokens_details": {"reasoning_tokens": 2},
                      "prompt_tokens_details": {"cached_tokens": 3}},
        }, "gen-abc", "vendor/model-v2")
        self.assertEqual(receipt["costUsd"], "0.0000004")
        self.assertEqual(receipt["costMicrousd"], 1)
        self.assertEqual(receipt["costRounding"], "ROUND_CEILING")
        self.assertEqual(receipt["tokenUsage"], {
            "prompt": 11, "completion": 7, "total": 18,
            "reasoning": 2, "cachedPrompt": 3,
        })

    def test_generation_metadata_reconciles_id_cost_and_model(self):
        payload = {"data": {"id": "gen-xyz", "model": "m", "tokens_prompt": 5,
                            "tokens_completion": 4, "total_cost": Decimal("0.25"),
                            "provider_name": "Provider"}}
        result = normalize_openrouter_receipt(payload, "gen-xyz", "m")
        self.assertEqual(result["receiptType"], "generation_metadata")
        self.assertEqual(result["costMicrousd"], 250000)
        self.assertEqual(result["tokenUsage"]["total"], 9)

    def test_generation_usage_amount_and_total_cost_must_agree(self):
        payload = {"data": {"id": "gen-x", "model": "m", "usage": Decimal("0.01"),
                            "total_cost": Decimal("0.01")}}
        result = normalize_openrouter_receipt(payload, "gen-x")
        self.assertEqual(result["costSource"], "data.total_cost+data.usage")
        payload["data"]["usage"] = Decimal("0.02")
        with self.assertRaises(ReceiptError):
            normalize_openrouter_receipt(payload, "gen-x")

    def test_missing_or_mismatched_generation_id_rejected(self):
        base = {"id": "gen-other", "model": "m", "usage": {"cost": Decimal("1")}}
        for expected in ("gen-wanted", ""):
            with self.subTest(expected=expected), self.assertRaises(ReceiptError):
                normalize_openrouter_receipt(base, expected)
        with self.assertRaises(ReceiptError):
            normalize_openrouter_receipt({"model": "m", "usage": {"cost": 1}}, "gen-wanted")

    def test_model_mismatch_conflicting_ids_and_currency_rejected(self):
        cases = [
            ({"id": "gen-a", "generation_id": "gen-b", "model": "m", "usage": {"cost": 1}}, "gen-a", None),
            ({"id": "gen-a", "model": "m", "usage": {"cost": 1, "currency": "EUR"}}, "gen-a", None),
            ({"id": "gen-a", "model": "other", "usage": {"cost": 1}}, "gen-a", "expected"),
        ]
        for payload, generation_id, expected_model in cases:
            with self.subTest(payload=payload), self.assertRaises(ReceiptError):
                normalize_openrouter_receipt(payload, generation_id, expected_model)

    def test_unknown_cost_and_bad_amounts_rejected(self):
        for payload in (
            {"id": "gen-a", "model": "m", "usage": {"prompt_tokens": 1}},
            {"id": "gen-a", "model": "m", "usage": {"cost": Decimal("-0.1")}},
            {"id": "gen-a", "model": "m", "usage": {"cost": Decimal("NaN")}},
            {"id": "gen-a", "model": "m", "usage": {"cost": True}},
        ):
            with self.subTest(payload=payload), self.assertRaises(ReceiptError):
                normalize_openrouter_receipt(payload, "gen-a")

    def test_token_count_conflicts_and_noninteger_values_rejected(self):
        for usage in (
            {"cost": 0, "prompt_tokens": -1},
            {"cost": 0, "prompt_tokens": 1.5},
            {"cost": 0, "prompt_tokens": 2, "completion_tokens": 3, "total_tokens": 9},
        ):
            with self.subTest(usage=usage), self.assertRaises(ReceiptError):
                normalize_openrouter_receipt({"id": "gen-a", "model": "m", "usage": usage}, "gen-a")

    def test_oversized_payload_rejected(self):
        with self.assertRaises(ReceiptError):
            normalize_openrouter_receipt({"id": "gen-a", "model": "m", "blob": "x" * (257 * 1024),
                                          "usage": {"cost": 0}}, "gen-a")

    def test_read_only_fetch_uses_fixed_origin_and_bounds(self):
        captured = {}
        body = json.dumps({"data": {"id": "gen-lookup", "model": "m",
                                    "total_cost": 0.004, "tokens_prompt": 4,
                                    "tokens_completion": 2}}).encode()
        def fetcher(url, headers, timeout, limit):
            captured.update(url=url, headers=dict(headers), timeout=timeout, limit=limit)
            return body
        receipt = reconcile_openrouter_generation("gen-lookup", "m", api_key="secret",
                                                  timeout_seconds=1, fetcher=fetcher)
        self.assertEqual(receipt["costMicrousd"], 4000)
        self.assertEqual(urlsplit(captured["url"]).scheme, "https")
        self.assertEqual(urlsplit(captured["url"]).netloc, "openrouter.ai")
        self.assertEqual(parse_qs(urlsplit(captured["url"]).query), {"id": ["gen-lookup"]})
        self.assertEqual(captured["headers"]["Authorization"], "Bearer secret")
        self.assertEqual(captured["limit"], 256 * 1024)
        self.assertNotIn("secret", json.dumps(receipt))

    def test_fetch_rejects_bad_json_mismatch_and_oversize(self):
        with self.assertRaises(ReceiptError):
            reconcile_openrouter_generation("gen-x", api_key="x", fetcher=lambda *_: b"{}")
        with self.assertRaises(ReceiptError):
            reconcile_openrouter_generation("gen-x", api_key="x", fetcher=lambda *_: b"x" * 20,
                                             max_response_bytes=10)
        with self.assertRaises(ReceiptError):
            reconcile_openrouter_generation("gen-x", api_key="x", fetcher=lambda *_: b"not-json")

    def test_cli_returns_only_normalized_metadata_and_sanitized_failure(self):
        result = cli_dispatch({"action": "normalizeOpenRouter", "expectedGenerationId": "gen-cli",
                               "payload": {"id": "gen-cli", "model": "m", "content": "private completion",
                                           "usage": {"cost": Decimal("0.1"), "prompt_tokens": 1}}})
        self.assertEqual(result["generationId"], "gen-cli")
        self.assertNotIn("content", result)
        self.assertNotIn("private completion", json.dumps(result))
        with self.assertRaises(ReceiptError):
            cli_dispatch({"action": "normalizeOpenRouter", "expectedGenerationId": "gen-cli",
                          "payload": {"id": "gen-cli", "model": "m", "usage": {"cost": 1}},
                          "apiKey": "must not be accepted"})


class VllmEstimateTests(unittest.TestCase):
    def test_exclusive_compute_and_amortized_estimate_are_separate(self):
        result = estimate_vllm_allocation_cost(
            gpu_count=2, gpu_hourly_rate_usd=Decimal("3"), allocated_seconds=600,
            allocation_mode="exclusive", amortized_gpu_hourly_rate_usd=Decimal("1.2"))
        self.assertEqual(result["billingStatus"], "not_billing")
        self.assertEqual(result["fullPoolComputeEstimateUsd"], "1")
        self.assertEqual(result["fullPoolAmortizedEstimateUsd"], "0.4")
        self.assertEqual(result["attributedTotalEstimateMicrousd"], 1_400_000)

    def test_shared_without_fraction_remains_unattributed(self):
        result = estimate_vllm_allocation_cost(
            gpu_count=4, gpu_hourly_rate_usd=2, allocated_seconds=1800,
            allocation_mode="shared")
        self.assertEqual(result["fullPoolComputeEstimateUsd"], "4")
        self.assertIsNone(result["attributedComputeEstimateMicrousd"])
        self.assertIsNone(result["attributedTotalEstimateMicrousd"])
        self.assertIn("cannot be attributed", result["uncertainty"])

    def test_shared_fraction_and_invalid_bounds(self):
        result = estimate_vllm_allocation_cost(
            gpu_count=2, gpu_hourly_rate_usd=Decimal("1"), allocated_seconds=3600,
            allocation_mode="shared", shared_fraction=Decimal("0.25"))
        self.assertEqual(result["attributedComputeEstimateUsd"], "0.50")
        with self.assertRaises(ReceiptError):
            estimate_vllm_allocation_cost(gpu_count=0, gpu_hourly_rate_usd=1,
                                          allocated_seconds=1, allocation_mode="exclusive")
        with self.assertRaises(ReceiptError):
            estimate_vllm_allocation_cost(gpu_count=1, gpu_hourly_rate_usd=1,
                                          allocated_seconds=1, allocation_mode="shared", shared_fraction=0)

    def test_cli_estimate_action(self):
        result = cli_dispatch({"action": "estimateVllmAllocation", "gpuCount": 1,
                               "gpuHourlyRateUsd": 1, "allocatedSeconds": 1,
                               "allocationMode": "exclusive"})
        self.assertEqual(result["billingStatus"], "not_billing")
        self.assertEqual(result["attributedComputeEstimateMicrousd"], 278)


if __name__ == "__main__":
    unittest.main()
