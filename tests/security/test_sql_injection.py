"""SQL injection prevention tests for ApexGraphSwarm.

Verifies that all database queries use parameterized statements
and that user input cannot inject SQL code.
"""
import re
import sqlite3
import tempfile
import unittest
from pathlib import Path

from apexgraphswarm.access import AccessDenied, authorize, initialize_access_schema
from apexgraphswarm.control import ControlError, ControlStore
from apexgraphswarm.identity import WorkerIdentityError, initialize_identity_schema, verify_credential
from apexgraphswarm.request_registry import register_hashed_request
from apexgraphswarm.specialist_access import SpecialistContractError, _identifier


class SQLInjectionControlStoreTests(unittest.TestCase):
    """ControlStore queries must use parameterized statements."""

    def test_create_run_with_sql_injection_in_id(self):
        """Run IDs with SQL metacharacters must be stored safely."""
        with ControlStore(":memory:") as store:
            plan = {"version": 1, "agents": [{"id": "a"}], "tasks": [
                {"id": "t", "agentId": "a", "payload": {},
                 "reservedCostMicrousd": 0, "executionClass": "fixture"}]}
            malicious_key = "'; DROP TABLE runs; --"
            run = store.create_run(plan, idempotency_key=malicious_key, budget_microusd=0)
            self.assertIsNotNone(run)
            status = store.status(run["run"]["id"])
            self.assertIsNotNone(status)

    def test_create_run_with_union_in_id(self):
        """UNION-based injection in idempotency key must be stored as data."""
        with ControlStore(":memory:") as store:
            plan = {"version": 1, "agents": [{"id": "a"}], "tasks": [
                {"id": "t", "agentId": "a", "payload": {},
                 "reservedCostMicrousd": 0, "executionClass": "fixture"}]}
            malicious_key = "' UNION SELECT * FROM workers; --"
            run = store.create_run(plan, idempotency_key=malicious_key, budget_microusd=0)
            self.assertIsNotNone(run)

    def test_claim_with_sql_injection_in_worker_id(self):
        """Worker IDs with SQL metacharacters must not inject."""
        with ControlStore(":memory:") as store:
            plan = {"version": 1, "agents": [{"id": "a"}], "tasks": [
                {"id": "t", "agentId": "a", "payload": {},
                 "reservedCostMicrousd": 0, "executionClass": "fixture"}]}
            run = store.create_run(plan, idempotency_key="test", budget_microusd=0)
            # The worker_id is used as a parameter in SQL queries
            # SQL injection attempts are stored as data, not executed
            task = store.claim(run["run"]["id"], "'; DROP TABLE tasks; --")
            self.assertIsNotNone(task)
            # Verify the table still exists
            status = store.status(run["run"]["id"])
            self.assertIsNotNone(status)

    def test_status_with_sql_injection_in_run_id(self):
        """status() with malicious run ID must not inject."""
        with ControlStore(":memory:") as store:
            result = store.status("'; DROP TABLE runs; --")
            self.assertIsNone(result)

    def test_grant_access_with_sql_injection_in_ids(self):
        """Access grant IDs with SQL metacharacters must be stored safely."""
        with ControlStore(":memory:") as store:
            plan = {"version": 1, "agents": [{"id": "a"}], "tasks": [
                {"id": "t", "agentId": "a", "payload": {},
                 "reservedCostMicrousd": 0, "executionClass": "fixture"}]}
            run = store.create_run(plan, idempotency_key="test", budget_microusd=0)
            with self.assertRaises(ControlError):
                store.grant_access(principal_id="'; DROP TABLE access_grants; --",
                                   tool_id="tool", resource_id="res",
                                   max_budget_microusd=10, expires_at=9999)

    def test_task_payload_with_sql_strings(self):
        """Task payloads containing SQL strings must be stored as data."""
        with ControlStore(":memory:") as store:
            plan = {"version": 1, "agents": [{"id": "a"}], "tasks": [
                {"id": "t", "agentId": "a",
                 "payload": {"query": "SELECT * FROM users; DROP TABLE users; --"},
                 "reservedCostMicrousd": 0, "executionClass": "fixture"}]}
            run = store.create_run(plan, idempotency_key="test", budget_microusd=0)
            status = store.status(run["run"]["id"])
            self.assertIsNotNone(status)

    def test_control_store_uses_parameterized_queries(self):
        """ControlStore source must use parameterized queries (no string formatting)."""
        control_file = Path(__file__).resolve().parent.parent.parent / "apexgraphswarm" / "control.py"
        if control_file.exists():
            content = control_file.read_text()
            # Check that execute calls use ? placeholders, not % or .format
            execute_calls = re.findall(r'\.execute\([^)]+\)', content)
            for call in execute_calls:
                # Should not use Python string formatting in SQL
                self.assertNotIn('%s', call,
                                 f"SQL query uses %%s instead of ?: {call}")
                self.assertNotIn('.format(', call,
                                 f"SQL query uses .format(): {call}")


class SQLInjectionAccessTests(unittest.TestCase):
    """Access control queries must use parameterized statements."""

    def test_authorize_with_sql_injection_in_principal(self):
        """authorize() with malicious principal_id must not inject."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "test.db")
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            initialize_access_schema(conn)
            conn.execute(
                "INSERT INTO access_grants (grant_id,principal_id,tool_id,resource_id,max_budget_microusd,expires_at,created_at) "
                "VALUES ('g1','alice','tool1','res1',100,9999.0,1.0)")
            conn.commit()

            with self.assertRaises(AccessDenied):
                authorize(conn, principal_id="alice' OR '1'='1",
                          tool_id="tool1", resource_id="res1",
                          budget_microusd=1, now=1.0)

            with self.assertRaises(AccessDenied):
                authorize(conn, principal_id="alice",
                          tool_id="tool1' OR '1'='1",
                          resource_id="res1", budget_microusd=1, now=1.0)

            with self.assertRaises(AccessDenied):
                authorize(conn, principal_id="alice",
                          tool_id="tool1", resource_id="res1' OR '1'='1",
                          budget_microusd=1, now=1.0)

            conn.close()

    def test_authorize_with_union_in_principal(self):
        """UNION-based injection in principal_id must not return grants."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "test.db")
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            initialize_access_schema(conn)
            conn.execute(
                "INSERT INTO access_grants (grant_id,principal_id,tool_id,resource_id,max_budget_microusd,expires_at,created_at) "
                "VALUES ('g1','alice','tool1','res1',100,9999.0,1.0)")
            conn.commit()

            with self.assertRaises(AccessDenied):
                authorize(conn, principal_id="nonexistent' UNION SELECT 'x','y','z','w' --",
                          tool_id="tool1", resource_id="res1",
                          budget_microusd=1, now=1.0)
            conn.close()

    def test_access_module_uses_parameterized_queries(self):
        """access.py must use parameterized queries."""
        access_file = Path(__file__).resolve().parent.parent.parent / "apexgraphswarm" / "access.py"
        if access_file.exists():
            content = access_file.read_text()
            # Check for ? placeholders in SQL
            self.assertIn('?', content,
                          "access.py should use ? placeholders in SQL queries")
            # Check no string formatting in execute calls
            execute_calls = re.findall(r'\.execute\([^)]+\)', content)
            for call in execute_calls:
                self.assertNotIn('%s', call,
                                 f"SQL query uses %%s instead of ?: {call}")


class SQLInjectionIdentityTests(unittest.TestCase):
    """Identity queries must use parameterized statements."""

    def test_verify_credential_with_sql_injection_in_worker_id(self):
        """verify_credential() with malicious worker_id must not inject."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "test.db")
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            initialize_identity_schema(conn)
            import hashlib, secrets
            token = secrets.token_urlsafe(32)
            conn.execute(
                "INSERT INTO workers (worker_id,principal_id,token_hash,expires_at,created_at) "
                "VALUES ('worker1','alice',?,9999.0,1.0)",
                (hashlib.sha256(token.encode()).hexdigest(),))
            conn.commit()

            with self.assertRaises(WorkerIdentityError):
                verify_credential(conn, worker_id="worker1' OR '1'='1",
                                 credential=token, now=1.0)

            conn.close()

    def test_verify_credential_with_union_in_worker_id(self):
        """UNION-based injection in worker_id must not authenticate."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "test.db")
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            initialize_identity_schema(conn)
            import hashlib, secrets
            token = secrets.token_urlsafe(32)
            conn.execute(
                "INSERT INTO workers (worker_id,principal_id,token_hash,expires_at,created_at) "
                "VALUES ('worker1','alice',?,9999.0,1.0)",
                (hashlib.sha256(token.encode()).hexdigest(),))
            conn.commit()

            with self.assertRaises(WorkerIdentityError):
                verify_credential(conn, worker_id="x' UNION SELECT 'worker1','alice',?,9999.0 --",
                                 credential=token, now=1.0)
            conn.close()

    def test_identity_module_uses_parameterized_queries(self):
        """identity.py must use parameterized queries."""
        identity_file = Path(__file__).resolve().parent.parent.parent / "apexgraphswarm" / "identity.py"
        if identity_file.exists():
            content = identity_file.read_text()
            self.assertIn('?', content,
                          "identity.py should use ? placeholders in SQL queries")


class SQLInjectionRequestRegistryTests(unittest.TestCase):
    """Request registry queries must use parameterized statements."""

    def test_register_with_sql_injection_in_hashes(self):
        """SQL injection in hash values must be rejected by validation."""
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "test.db")
            with self.assertRaises(ValueError):
                register_hashed_request(path,
                                        request_key_hash="'; DROP TABLE integration_request_registry; --",
                                        scope_hash="a" * 64,
                                        payload_digest="b" * 64,
                                        candidate_job_id="12345678-1234-1234-1234-123456789012")

    def test_register_with_union_in_hashes(self):
        """UNION injection in hash values must be rejected."""
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "test.db")
            with self.assertRaises(ValueError):
                register_hashed_request(path,
                                        request_key_hash="a" * 64,
                                        scope_hash="b' UNION SELECT 'x','y','z' --",
                                        payload_digest="b" * 64,
                                        candidate_job_id="12345678-1234-1234-1234-123456789012")

    def test_request_registry_uses_parameterized_queries(self):
        """request_registry.py must use parameterized queries."""
        registry_file = Path(__file__).resolve().parent.parent.parent / "apexgraphswarm" / "request_registry.py"
        if registry_file.exists():
            content = registry_file.read_text()
            self.assertIn('?', content,
                          "request_registry.py should use ? placeholders in SQL queries")


class SQLInjectionSpecialistAccessTests(unittest.TestCase):
    """Specialist contract queries must use parameterized statements."""

    def test_contract_with_sql_injection_in_ids(self):
        """Contract IDs with SQL metacharacters must be validated."""
        with self.assertRaises(SpecialistContractError):
            _identifier("'; DROP TABLE contracts; --", "test")
        with self.assertRaises(SpecialistContractError):
            _identifier("id' OR '1'='1", "test")

    def test_specialist_access_uses_parameterized_queries(self):
        """specialist_access.py must use parameterized queries."""
        specialist_file = Path(__file__).resolve().parent.parent.parent / "apexgraphswarm" / "specialist_access.py"
        if specialist_file.exists():
            content = specialist_file.read_text()
            # Check for ? placeholders in SQL execute calls
            execute_calls = re.findall(r'\.execute\([^)]+\)', content)
            for call in execute_calls:
                self.assertNotIn('%s', call,
                                 f"SQL query uses %%s instead of ?: {call}")
                self.assertNotIn('.format(', call,
                                 f"SQL query uses .format(): {call}")


class SQLInjectionNeo4jStoreTests(unittest.TestCase):
    """Neo4j store queries must use parameterized statements."""

    def test_neo4j_store_uses_parameters(self):
        """Neo4j store must use parameterized queries."""
        neo4j_file = Path(__file__).resolve().parent.parent.parent / "apps" / "web" / "lib" / "neo4j-store.ts"
        if neo4j_file.exists():
            content = neo4j_file.read_text()
            # Neo4j driver uses parameters object
            self.assertIn('parameters', content,
                          "Neo4j store must use parameters")
            # Should not concatenate user input into Cypher
            self.assertNotIn('statement +', content,
                             "Neo4j store should not concatenate into statements")


if __name__ == '__main__':
    unittest.main()
