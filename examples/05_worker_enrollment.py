"""Example 05: Worker enrollment and authentication.

Workers are enrolled with a principal identity and receive
an opaque credential exactly once. Credentials are never stored
in plain text — only SHA-256 digests.
"""
import time
from apexgraphswarm.control import ControlStore

store = ControlStore(":memory:")

# Enroll a worker
expires_at = time.time() + 3600  # 1 hour
worker = store.enroll_worker(
    worker_id="worker-alpha",
    principal_id="principal-1",
    expires_at=expires_at,
)
print(f"Enrolled worker: {worker['workerId']}")
print(f"Principal: {worker['principalId']}")
print(f"Expires: {worker['expiresAt']}")
print(f"Credential: {worker['credential'][:20]}... (show once, never stored)")

# Authenticate with the credential
claim = store.claim(
    "some-run-id",  # would be a real run
    "worker-alpha",
    _credential=worker["credential"],
    _require_identity=True,
)
# (This will fail because the run doesn't exist, but shows the pattern)

# Revoke a worker
revoked = store.revoke_worker("worker-alpha")
print(f"Worker revoked: {revoked}")

store.close()
