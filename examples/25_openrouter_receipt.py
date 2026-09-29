"""Example 25: OpenRouter receipt normalization.

Normalize provider receipts with generation ID reconciliation,
cost extraction, and token usage tracking.
"""
from apexgraphswarm.provider_receipts import normalize_openrouter_receipt

# Simulated OpenRouter completion response
payload = {
    "id": "gen-abc123",
    "model": "openai/gpt-4",
    "usage": {
        "prompt_tokens": 150,
        "completion_tokens": 300,
        "total_tokens": 450,
        "cost": 0.0045,
        "completion_tokens_details": {"reasoning_tokens": 50},
        "prompt_tokens_details": {"cached_tokens": 100},
    },
    "currency": "USD",
}

receipt = normalize_openrouter_receipt(
    payload,
    expected_generation_id="gen-abc123",
    expected_model="openai/gpt-4",
)

print(f"Provider: {receipt['provider']}")
print(f"Receipt type: {receipt['receiptType']}")
print(f"Generation ID: {receipt['generationId']}")
print(f"Model: {receipt['model']}")
print(f"Cost: ${receipt['costUsd']} ({receipt['costMicrousd']} micro-USD)")
print(f"Cost source: {receipt['costSource']}")
print(f"Token usage:")
print(f"  Prompt: {receipt['tokenUsage']['prompt']}")
print(f"  Completion: {receipt['tokenUsage']['completion']}")
print(f"  Total: {receipt['tokenUsage']['total']}")
print(f"  Reasoning: {receipt['tokenUsage']['reasoning']}")
print(f"  Cached prompt: {receipt['tokenUsage']['cachedPrompt']}")
print(f"Reconciliation: {receipt['reconciliation']}")
