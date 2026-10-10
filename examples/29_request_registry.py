"""Example 29: Request registry for idempotent integrations.

Crash-safe, fail-closed idempotency registry for integration
HTTP requests. Only SHA-256 digests are persisted.
"""
import hashlib
import uuid
from apexgraphswarm.request_registry import register_hashed_request, lookup_durable_run_id

# Hash the request components
request_key = "user-123:create-invoice"
scope_hash = hashlib.sha256(b"tenant-456").hexdigest()
request_key_hash = hashlib.sha256(request_key.encode()).hexdigest()
payload = {"amount": 100, "currency": "USD"}
payload_digest = hashlib.sha256(str(payload).encode()).hexdigest()
job_id = str(uuid.uuid4())

# Register the request
result = register_hashed_request(
    ":memory:",
    request_key_hash=request_key_hash,
    scope_hash=scope_hash,
    payload_digest=payload_digest,
    candidate_job_id=job_id,
)
print(f"Created: {result['created']}")
print(f"Job ID: {result['jobId']}")

# Register again with same key (idempotent)
result2 = register_hashed_request(
    ":memory:",
    request_key_hash=request_key_hash,
    scope_hash=scope_hash,
    payload_digest=payload_digest,
    candidate_job_id=str(uuid.uuid4()),
)
print(f"Second call created: {result2['created']}")
print(f"Same job ID: {result2['jobId'] == result['jobId']}")

# Look up the durable run
run_id = lookup_durable_run_id(":memory:", job_id)
print(f"Durable run ID: {run_id}")
