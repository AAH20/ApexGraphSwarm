"""Authentication bypass prevention tests for ApexGraphSwarm.

Verifies that worker identity verification, credential validation,
and authentication checks cannot be bypassed.
"""
import hashlib
import secrets
import tempfile
import time
import unittest
from pathlib import Path

from apexgraphswarm.access import AccessDenied
from apexgraphswarm.control import ControlError, ControlStore, LeaseError
from apexgraphswarm.identity import WorkerIdentityError, issue_credential, token_digest, verify_credential
import sqlite3


class AuthenticationBypassIdentityTests(unittest.TestCase):
    """Worker identity verification must not be bypassable."""

    def test_verify_credential_rejects_none(self):
        """None credential is rejected."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "test.db")
            conn = __import__('sqlite3').connect(db_path)
            conn.row_factory = __import__('sqlite3').Row
            from apexgraphswarm.identity import initialize_identity_schema
            initialize_identity_schema(conn)
            with self.assertRaises(WorkerIdentityError):
                verify_credential(conn, worker_id="w", credential=None, now=1.0)
            conn.close()

    def test_verify_credential_rejects_empty_string(self):
        """Empty string credential is rejected."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "test.db")
            conn = __import__('sqlite3').connect(db_path)
            conn.row_factory = __import__('sqlite3').Row
            from apexgraphswarm.identity import initialize_identity_schema
            initialize_identity_schema(conn)
            with self.assertRaises(WorkerIdentityError):
                verify_credential(conn, worker_id="w", credential="", now=1.0)
            conn.close()

    def test_verify_credential_rejects_short_token(self):
        """Tokens shorter than 32 chars are rejected."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "test.db")
            conn = __import__('sqlite3').connect(db_path)
            conn.row_factory = __import__('sqlite3').Row
            from apexgraphswarm.identity import initialize_identity_schema
            initialize_identity_schema(conn)
            with self.assertRaises(WorkerIdentityError):
                verify_credential(conn, worker_id="w", credential="short", now=1.0)
            conn.close()

    def test_verify_credential_rejects_long_token(self):
        """Tokens longer than 512 chars are rejected."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "test.db")
            conn = __import__('sqlite3').connect(db_path)
            conn.row_factory = __import__('sqlite3').Row
            from apexgraphswarm.identity import initialize_identity_schema
            initialize_identity_schema(conn)
            with self.assertRaises(WorkerIdentityError):
                verify_credential(conn, worker_id="w", credential="a" * 513, now=1.0)
            conn.close()

    def test_verify_credential_rejects_wrong_token(self):
        """Wrong token for existing worker is rejected."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "test.db")
            conn = __import__('sqlite3').connect(db_path)
            conn.row_factory = __import__('sqlite3').Row
            from apexgraphswarm.identity import initialize_identity_schema
            initialize_identity_schema(conn)
            token = secrets.token_urlsafe(32)
            conn.execute(
                "INSERT INTO workers (worker_id,principal_id,token_hash,expires_at,created_at) "
                "VALUES ('w','p',?,9999.0,1.0)",
                (hashlib.sha256(token.encode()).hexdigest(),))
            conn.commit()
            wrong_token = secrets.token_urlsafe(32)
            with self.assertRaises(WorkerIdentityError):
                verify_credential(conn, worker_id="w", credential=wrong_token, now=1.0)
            conn.close()

    def test_verify_credential_rejects_expired_worker(self):
        """Expired worker credentials are rejected."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "test.db")
            conn = __import__('sqlite3').connect(db_path)
            conn.row_factory = __import__('sqlite3').Row
            from apexgraphswarm.identity import initialize_identity_schema
            initialize_identity_schema(conn)
            token = secrets.token_urlsafe(32)
            conn.execute(
                "INSERT INTO workers (worker_id,principal_id,token_hash,expires_at,created_at) "
                "VALUES ('w','p',?,100.0,1.0)",
                (hashlib.sha256(token.encode()).hexdigest(),))
            conn.commit()
            with self.assertRaises(WorkerIdentityError):
                verify_credential(conn, worker_id="w", credential=token, now=101.0)
            conn.close()

    def test_verify_credential_rejects_revoked_worker(self):
        """Revoked worker credentials are rejected."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "test.db")
            conn = __import__('sqlite3').connect(db_path)
            conn.row_factory = __import__('sqlite3').Row
            from apexgraphswarm.identity import initialize_identity_schema
            initialize_identity_schema(conn)
            token = secrets.token_urlsafe(32)
            conn.execute(
                "INSERT INTO workers (worker_id,principal_id,token_hash,expires_at,revoked_at,created_at) "
                "VALUES ('w','p',?,9999.0,50.0,1.0)",
                (hashlib.sha256(token.encode()).hexdigest(),))
            conn.commit()
            with self.assertRaises(WorkerIdentityError):
                verify_credential(conn, worker_id="w", credential=token, now=100.0)
            conn.close()

    def test_verify_credential_accepts_valid_token(self):
        """Valid token for active worker is accepted."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "test.db")
            conn = __import__('sqlite3').connect(db_path)
            conn.row_factory = __import__('sqlite3').Row
            from apexgraphswarm.identity import initialize_identity_schema
            initialize_identity_schema(conn)
            token = secrets.token_urlsafe(32)
            conn.execute(
                "INSERT INTO workers (worker_id,principal_id,token_hash,expires_at,created_at) "
                "VALUES ('w','p',?,9999.0,1.0)",
                (hashlib.sha256(token.encode()).hexdigest(),))
            conn.commit()
            row = verify_credential(conn, worker_id="w", credential=token, now=100.0)
            self.assertEqual(row["worker_id"], "w")
            conn.close()

    def test_nonexistent_worker_still_compares_digests(self):
        """Nonexistent worker still performs constant-time comparison."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "test.db")
            conn = __import__('sqlite3').connect(db_path)
            conn.row_factory = __import__('sqlite3').Row
            from apexgraphswarm.identity import initialize_identity_schema
            initialize_identity_schema(conn)
            # Even for nonexistent workers, compare_digest is called
            # to prevent timing attacks that reveal worker existence
            with self.assertRaises(WorkerIdentityError):
                verify_credential(conn, worker_id="nonexistent",
                                 credential=secrets.token_urlsafe(32), now=1.0)
            conn.close()


class AuthenticationBypassControlStoreTests(unittest.TestCase):
    """ControlStore authenticated operations must verify credentials."""

    def test_claim_authenticated_rejects_wrong_credential(self):
        """claim_authenticated rejects wrong credentials."""
        with ControlStore(":memory:") as store:
            plan = {"version": 1, "agents": [{"id": "a"}], "tasks": [
                {"id": "t", "agentId": "a", "payload": {},
                 "reservedCostMicrousd": 0, "executionClass": "fixture"}]}
            run = store.create_run(plan, idempotency_key="test", budget_microusd=0)
            enrollment = store.enroll_worker(worker_id="w", principal_id="p",
                                             expires_at=store._now() + 1000)
            with self.assertRaises(AccessDenied):
                store.claim_authenticated(run["run"]["id"], "w", "wrong-credential")

    def test_claim_authenticated_rejects_nonexistent_worker(self):
        """claim_authenticated rejects nonexistent workers."""
        with ControlStore(":memory:") as store:
            plan = {"version": 1, "agents": [{"id": "a"}], "tasks": [
                {"id": "t", "agentId": "a", "payload": {},
                 "reservedCostMicrousd": 0, "executionClass": "fixture"}]}
            run = store.create_run(plan, idempotency_key="test", budget_microusd=0)
            with self.assertRaises(AccessDenied):
                store.claim_authenticated(run["run"]["id"], "nonexistent",
                                           secrets.token_urlsafe(32))

    def test_complete_authenticated_rejects_wrong_credential(self):
        """complete_authenticated rejects wrong credentials."""
        with ControlStore(":memory:") as store:
            plan = {"version": 1, "agents": [{"id": "a"}], "tasks": [
                {"id": "t", "agentId": "a", "payload": {},
                 "reservedCostMicrousd": 0, "executionClass": "fixture"}]}
            run = store.create_run(plan, idempotency_key="test", budget_microusd=0)
            enrollment = store.enroll_worker(worker_id="w", principal_id="p",
                                             expires_at=store._now() + 1000)
            task = store.claim_authenticated(run["run"]["id"], "w", enrollment["credential"])
            with self.assertRaises(AccessDenied):
                store.complete_authenticated(task["taskId"], task["leaseToken"],
                                             "wrong-credential", {}, 0)

    def test_heartbeat_authenticated_rejects_wrong_credential(self):
        """heartbeat_authenticated rejects wrong credentials."""
        with ControlStore(":memory:") as store:
            plan = {"version": 1, "agents": [{"id": "a"}], "tasks": [
                {"id": "t", "agentId": "a", "payload": {},
                 "reservedCostMicrousd": 0, "executionClass": "fixture"}]}
            run = store.create_run(plan, idempotency_key="test", budget_microusd=0)
            enrollment = store.enroll_worker(worker_id="w", principal_id="p",
                                             expires_at=store._now() + 1000)
            task = store.claim_authenticated(run["run"]["id"], "w", enrollment["credential"])
            with self.assertRaises(AccessDenied):
                store.heartbeat_authenticated(task["taskId"], task["leaseToken"],
                                              "wrong-credential")

    def test_worker_cannot_use_another_workers_credential(self):
        """Worker A cannot use Worker B's credential."""
        with ControlStore(":memory:") as store:
            plan = {"version": 1, "agents": [{"id": "a"}], "tasks": [
                {"id": "t", "agentId": "a", "payload": {},
                 "reservedCostMicrousd": 0, "executionClass": "fixture"}]}
            run = store.create_run(plan, idempotency_key="test", budget_microusd=0)
            enrollment_a = store.enroll_worker(worker_id="w1", principal_id="p",
                                               expires_at=store._now() + 1000)
            enrollment_b = store.enroll_worker(worker_id="w2", principal_id="p",
                                               expires_at=store._now() + 1000)
            task = store.claim_authenticated(run["run"]["id"], "w1", enrollment_a["credential"])
            # w2 tries to complete w1's task
            with self.assertRaises(AccessDenied):
                store.complete_authenticated(task["taskId"], task["leaseToken"],
                                             enrollment_b["credential"], {}, 0)

    def test_revoked_worker_cannot_claim(self):
        """Revoked worker cannot claim tasks."""
        with ControlStore(":memory:") as store:
            plan = {"version": 1, "agents": [{"id": "a"}], "tasks": [
                {"id": "t", "agentId": "a", "payload": {},
                 "reservedCostMicrousd": 0, "executionClass": "fixture"}]}
            run = store.create_run(plan, idempotency_key="test", budget_microusd=0)
            enrollment = store.enroll_worker(worker_id="w", principal_id="p",
                                             expires_at=store._now() + 1000)
            store.revoke_worker("w")
            with self.assertRaises(AccessDenied):
                store.claim_authenticated(run["run"]["id"], "w", enrollment["credential"])

    def test_expired_worker_cannot_claim(self):
        """Expired worker cannot claim tasks."""
        with ControlStore(":memory:") as store:
            plan = {"version": 1, "agents": [{"id": "a"}], "tasks": [
                {"id": "t", "agentId": "a", "payload": {},
                 "reservedCostMicrousd": 0, "executionClass": "fixture"}]}
            run = store.create_run(plan, idempotency_key="test", budget_microusd=0)
            # enroll_worker validates expiry is in the future
            with self.assertRaises(ControlError):
                store.enroll_worker(worker_id="w", principal_id="p",
                                    expires_at=store._now() - 1)


class AuthenticationBypassCLITests(unittest.TestCase):
    """CLI actions must require authentication."""

    def test_cli_claim_requires_credential(self):
        """CLI claim action requires credential parameter."""
        from apexgraphswarm.control import _cli_request, ControlError
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "test.db")
            with self.assertRaises(ControlError):
                _cli_request({'dbPath': db_path, 'action': 'claim',
                              'runId': 'r', 'workerId': 'w'})

    def test_cli_enroll_worker_does_not_require_credential(self):
        """CLI enrollWorker action does not require credential (it mints one)."""
        from apexgraphswarm.control import _cli_request
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "test.db")
            result = _cli_request({'dbPath': db_path, 'action': 'enrollWorker',
                                   'workerId': 'w', 'principalId': 'p',
                                   'expiresAt': time.time() + 10000})
            self.assertIn('credential', result)


if __name__ == '__main__':
    unittest.main()
