"""Example 59: Advanced - security hardening.

Security best practices for production deployments.
"""
import os
import hashlib
import secrets
from apexgraphswarm.control import ControlStore

class SecurityManager:
    """Manage security aspects of the control plane."""

    def __init__(self, store: ControlStore):
        self.store = store

    def validate_environment(self):
        """Validate security-related environment variables."""
        issues = []

        # Check for secure database path
        db_path = os.environ.get("APEX_CONTROL_DB", "")
        if db_path and not db_path.startswith(("/var/lib/", "/data/")):
            issues.append(f"Database path {db_path} is not in a secure location")

        # Check for token in environment
        if "INTEGRATION_ACCESS_TOKEN" in os.environ:
            issues.append("INTEGRATION_ACCESS_TOKEN should not be in environment variables")

        # Check file permissions
        if db_path and os.path.exists(db_path):
            stat = os.stat(db_path)
            if stat.st_mode & 0o077:
                issues.append(f"Database file {db_path} has overly permissive permissions")

        return issues

    def rotate_worker_credentials(self, worker_id: str):
        """Rotate credentials for a worker."""
        # Revoke old worker
        self.store.revoke_worker(worker_id)

        # Enroll with new credential
        import time
        return self.store.enroll_worker(
            worker_id=worker_id,
            principal_id="principal-1",  # Would be looked up
            expires_at=time.time() + 3600,
        )

    def audit_access_grants(self):
        """Audit all active access grants."""
        # This would query the database directly
        # For now, return a placeholder
        return {
            "active_grants": 0,
            "expired_grants": 0,
            "revoked_grants": 0,
            "recommendations": [],
        }

    def generate_secure_id(self, prefix: str = "") -> str:
        """Generate a cryptographically secure ID."""
        random_part = secrets.token_urlsafe(16)
        if prefix:
            return f"{prefix}-{random_part}"
        return random_part

# Example usage
store = ControlStore(":memory:")
security = SecurityManager(store)

# Validate environment
issues = security.validate_environment()
if issues:
    print("Security issues found:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("Environment security: OK")

# Generate secure IDs
print(f"\nSecure IDs:")
print(f"  Run ID: {security.generate_secure_id('run')}")
print(f"  Task ID: {security.generate_secure_id('task')}")
print(f"  Worker ID: {security.generate_secure_id('worker')}")

# Audit
audit = security.audit_access_grants()
print(f"\nAccess grant audit: {audit}")

store.close()
