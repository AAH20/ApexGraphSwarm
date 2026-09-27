# Optional local decision providers

The decision gallery can compare Laya and AnyJev as typed decision providers. They return bounded choices, binary answers, or scores with probability distributions. They are decision components; neither is a drop-in substitute for a generative reviewer that writes explanations, plans, or code. The app estimates a per-question cost from operator configuration, while provider-reported token/cost usage remains unknown unless the provider returns it. The configured estimate is a preflight admission bound, not a provider-enforced billing cap.

## AnyJev L0 loopback bridge

`integrations/anyjev_bridge.py` is an optional, separately launched process. It is not imported by the stdlib control plane and does not start automatically. The bridge binds only to `127.0.0.1`, requires a bearer token, and accepts only `POST /v1/systemone` from loopback clients. It limits bodies to 64 KiB, state to 16,000 characters, requests to eight questions, and total decision options to 32. Inference is serialized; a timed-out inference retains its slot until the underlying call drains, preventing overlapping inference after a timeout response.

Create a dedicated environment for the optional model-serving stack. AnyJev currently publishes version `0.1.0`; the following pin reflects its current project metadata and should be checked against the official repository before upgrading:

```sh
python3 -m venv .venv-anyjev
. .venv-anyjev/bin/activate
python -m pip install 'anyjev[hf]==0.1.0' vllm
```

Start a local vLLM generation server separately. Use a model available to that server and tokenizer metadata accessible to the bridge process (a local model directory or an already available tokenizer cache):

```sh
vllm serve /absolute/path/to/model --task generate
```

Configure the bridge and the web app with the same random secret. Keep it in private environment files and out of version control:

```sh
export ANYJEV_BRIDGE_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export ANYJEV_MODEL='/absolute/path/to/model'
export ANYJEV_VLLM_URL='http://127.0.0.1:8000'
python integrations/anyjev_bridge.py --port 8766
```

Set the web app's `ANYJEV_PREDICT_URL=http://127.0.0.1:8766/v1/systemone`, `ANYJEV_API_KEY` to the same token, and `ANYJEV_COST_MICROUSD_PER_QUESTION` to a non-negative integer estimate. A value of zero is allowed only as an explicit estimate; it does not assert that the model is free. Do not set a remote URL: the bridge itself only accepts a loopback vLLM origin.

The endpoint accepts a compact Laya-shaped subset:

```json
{
  "state": "A user reports two charges for one order.",
  "questions": {
    "route": {
      "type": "choice",
      "instructions": "Choose a support team.",
      "criteria": {"billing": "Payment issues", "technical": "Product defects"}
    },
    "urgent": {"type": "noul", "instructions": "Does this require immediate escalation?"},
    "severity": {"type": "score", "instructions": "Rate severity.", "criteria": ["low", "medium", "high"]}
  }
}
```

`choice` criteria may be a string list or a label-to-description object (2–26 options). `score` criteria use the same shapes for 2–10 ordered levels; its numeric value is AnyJev's expected level index from zero through the last level index. `noul` takes no criteria and is returned as probability of true with `distribution: {"false": ..., "true": ...}`. The response contains `model`, keyed `answers` with `type`, `value`, `confidence`, and `distribution`, and `routing.level: "L0"`. `usage` is `null`: AnyJev's `Decision` object does not report token counts. The bridge never substitutes zero usage or cost.

The bridge uses AnyJev's `Decider(..., level="L0")` and `Question.choice`, `.score(levels=...)`, and `.noul` APIs. This is the zero-label L0 route only: the bridge does not load calibration artifacts or fit L2 heads. L0 confidence is a probability from the decision model, not a guarantee that the decision is safe; configure thresholds and human review for the use case. The bridge returns generic upstream errors and does not echo prompts, upstream payloads, or exception text. Its bearer token protects the local endpoint, but loopback binding is not a substitute for host security.

## Laya

Laya's documented serving route is `POST /v1/systemone`, which accepts a state and typed questions and returns model answers, confidence/probabilities, usage, and routing metadata. The app can be pointed at an operator-configured Laya server with `LAYA_PREDICT_URL` and `LAYA_API_KEY`. Review the Laya server's own model, concurrency, and request-size settings; do not assume its confidence values calibrate identically to AnyJev. Laya documents confidence as normalized entropy, whereas AnyJev exposes its maximum typed-option probability.

## Scope and provenance

AnyJev is Apache-2.0 licensed and lists Python 3.10+; current project metadata pins version `0.1.0`. Its vLLM backend uses generation for raw/L0/L1 and an embedding server for L2. This bridge deliberately selects only L0, so it requires a generation server (`--task generate`) and does not claim an L2 head or calibration. AnyJev's README describes individual typed-decision evaluation and calls agent-loop evaluation future work; do not present those standalone results as ApexGraphSwarm workflow benchmarks. Model availability, tokenizer access, GPU capacity, and latency are local deployment requirements and were not exercised by the fake-backed bridge tests.

Primary sources, checked 2026-09-27: [AnyJev README and API example](https://github.com/nokia-applied-research/AnyJev/blob/main/README.md), [AnyJev `Question` API](https://github.com/nokia-applied-research/AnyJev/blob/main/anyjev/question.py), [AnyJev result fields](https://github.com/nokia-applied-research/AnyJev/blob/main/anyjev/result.py), [AnyJev vLLM backend](https://github.com/nokia-applied-research/AnyJev/blob/main/anyjev/backends/vllm.py), [AnyJev package metadata](https://github.com/nokia-applied-research/AnyJev/blob/main/pyproject.toml), [AnyJev license](https://github.com/nokia-applied-research/AnyJev/blob/main/LICENSE), [Laya serving docs](https://github.com/NandhaKishorM/laya), and [Laya HTTP server](https://github.com/NandhaKishorM/laya/blob/main/laya/serve.py).

### Estimate calibration

The dashboard multiplies the configured conservative per-question estimate by
the submitted question count. AnyJev L0 can perform multiple prefills per question
as option count and permutation settings change. Calibrate this estimate against
your maximum permitted option count, context length and backend settings; it is
not an exact token quote or a hard cap on provider billing. Compare measured
latency and held-out decision quality on the same inputs before choosing a route.
