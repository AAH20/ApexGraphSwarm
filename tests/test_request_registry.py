import hashlib
import sqlite3
import tempfile
import threading
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from apexgraphswarm.request_registry import (RequestConflictError, lookup_durable_run_id,
                                             register_hashed_request)


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


class RequestRegistryTests(unittest.TestCase):
    def test_entry_survives_reopen_and_never_persists_raw_request_data(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "control.sqlite"
            args = dict(request_key_hash=digest("raw-idempotency-key"),
                        scope_hash=digest("private-server-token"),
                        payload_digest=digest('{"goal":"do not persist me"}'))
            first_id = str(uuid.uuid4())
            first = register_hashed_request(path, **args, candidate_job_id=first_id)
            self.assertEqual(first, {"created": True, "jobId": first_id})
            after_restart = register_hashed_request(path, **args,
                                                    candidate_job_id=str(uuid.uuid4()))
            self.assertEqual(after_restart, {"created": False, "jobId": first_id})
            connection = sqlite3.connect(path)
            try:
                columns = [row[1] for row in connection.execute(
                    "PRAGMA table_info(integration_request_registry)")]
                self.assertEqual(columns, ["scope_hash", "request_key_hash", "payload_digest", "job_id"])
                stored = repr(connection.execute(
                    "SELECT * FROM integration_request_registry").fetchone())
                self.assertNotIn("raw-idempotency-key", stored)
                self.assertNotIn("private-server-token", stored)
                self.assertNotIn("do not persist me", stored)
            finally:
                connection.close()

    def test_same_scoped_key_with_changed_body_conflicts(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "requests.sqlite"
            common = {"request_key_hash": digest("request-key"), "scope_hash": digest("workspace")}
            register_hashed_request(path, **common, payload_digest=digest("body-a"),
                                    candidate_job_id=str(uuid.uuid4()))
            with self.assertRaises(RequestConflictError):
                register_hashed_request(path, **common, payload_digest=digest("body-b"),
                                        candidate_job_id=str(uuid.uuid4()))
            # A different authenticated scope gets an independent namespace.
            scoped = register_hashed_request(path, request_key_hash=common["request_key_hash"],
                                              scope_hash=digest("other-workspace"),
                                              payload_digest=digest("body-b"),
                                              candidate_job_id=str(uuid.uuid4()))
            self.assertTrue(scoped["created"])

    def test_concurrent_contenders_converge_on_one_stable_job_id(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "concurrent.sqlite"
            common = {"request_key_hash": digest("same-key"), "scope_hash": digest("same-scope"),
                      "payload_digest": digest("same-body")}
            candidates = [str(uuid.uuid4()) for _ in range(12)]
            barrier = threading.Barrier(len(candidates))

            def contender(candidate):
                barrier.wait()
                return register_hashed_request(path, **common, candidate_job_id=candidate)

            with ThreadPoolExecutor(max_workers=len(candidates)) as pool:
                results = list(pool.map(contender, candidates))
            self.assertEqual(len({result["jobId"] for result in results}), 1)
            self.assertEqual(sum(result["created"] for result in results), 1)
            connection = sqlite3.connect(path)
            try:
                self.assertEqual(connection.execute(
                    "SELECT COUNT(*) FROM integration_request_registry").fetchone()[0], 1)
            finally:
                connection.close()

    def test_invalid_digests_and_job_ids_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.sqlite"
            with self.assertRaises(ValueError):
                register_hashed_request(path, request_key_hash="raw-key", scope_hash=digest("scope"),
                                        payload_digest=digest("body"), candidate_job_id=str(uuid.uuid4()))
            with self.assertRaises(ValueError):
                register_hashed_request(path, request_key_hash=digest("key"), scope_hash=digest("scope"),
                                        payload_digest=digest("body"), candidate_job_id="not-a-job")

    def test_recovery_lookup_returns_only_existing_durable_run_id(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "control.sqlite"
            job_id = str(uuid.uuid4())
            self.assertIsNone(lookup_durable_run_id(path, job_id))
            connection = sqlite3.connect(path)
            try:
                connection.execute("CREATE TABLE runs(id TEXT PRIMARY KEY,idempotency_key TEXT UNIQUE)")
                connection.execute("INSERT INTO runs VALUES(?,?)", ("durable-run-1", f"integration-{job_id}"))
                connection.commit()
            finally:
                connection.close()
            self.assertEqual(lookup_durable_run_id(path, job_id), "durable-run-1")


if __name__ == "__main__":
    unittest.main()
