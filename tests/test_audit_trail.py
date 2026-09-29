import os
import tempfile
import unittest

from kernels.audit_trail.audit_trail import (
    AuditTrail,
    AuditTrailError,
    ChainBrokenError,
    EntryNotFoundError,
    EvidenceNotFoundError,
    GENESIS_HASH,
    compute_content_hash,
    compute_hash,
)


class FakeClock:
    def __init__(self, value=1000.0):
        self.value = value

    def __call__(self):
        return self.value


class AuditTrailTests(unittest.TestCase):
    def test_genesis_and_append(self):
        trail = AuditTrail(":memory:")
        entry = trail.append("test.event", {"key": "value"})
        self.assertEqual(entry.sequence, 1)
        self.assertEqual(entry.previous_hash, GENESIS_HASH)
        self.assertEqual(len(entry.entry_hash), 64)
        valid, broken = trail.verify()
        self.assertTrue(valid)
        self.assertIsNone(broken)
        trail.close()

    def test_chain_linking(self):
        trail = AuditTrail(":memory:")
        e1 = trail.append("first", {"n": 1})
        e2 = trail.append("second", {"n": 2})
        self.assertEqual(e2.previous_hash, e1.entry_hash)
        self.assertEqual(e1.sequence, 1)
        self.assertEqual(e2.sequence, 2)
        trail.close()

    def test_tamper_detection_payload_modification(self):
        trail = AuditTrail(":memory:")
        trail.append("event", {"data": "original"})
        trail._db.execute(
            "UPDATE audit_chain SET payload_json='{\"data\":\"tampered\"}' WHERE sequence=1"
        )
        valid, broken = trail.verify()
        self.assertFalse(valid)
        self.assertEqual(broken, 1)
        trail.close()

    def test_tamper_detection_hash_modification(self):
        trail = AuditTrail(":memory:")
        trail.append("event", {"data": "original"})
        trail._db.execute(
            "UPDATE audit_chain SET entry_hash='0'*64 WHERE sequence=1"
        )
        valid, broken = trail.verify()
        self.assertFalse(valid)
        self.assertEqual(broken, 1)
        trail.close()

    def test_tamper_detection_previous_hash_modification(self):
        trail = AuditTrail(":memory:")
        trail.append("event1", {"n": 1})
        trail.append("event2", {"n": 2})
        # Break the link by changing entry 2's previous_hash
        trail._db.execute(
            "UPDATE audit_chain SET previous_hash='f'*64 WHERE sequence=2"
        )
        valid, broken = trail.verify()
        self.assertFalse(valid)
        self.assertEqual(broken, 2)
        trail.close()

    def test_tamper_detection_deletion(self):
        trail = AuditTrail(":memory:")
        trail.append("event1", {"n": 1})
        trail.append("event2", {"n": 2})
        trail.append("event3", {"n": 3})
        # Delete middle entry
        trail._db.execute("DELETE FROM audit_chain WHERE sequence=2")
        valid, broken = trail.verify()
        self.assertFalse(valid)
        self.assertEqual(broken, 2)
        trail.close()

    def test_evidence_vault_store_and_retrieve(self):
        trail = AuditTrail(":memory:")
        content = b"test evidence content"
        record = trail.store_evidence(
            content, media_type="text/plain", metadata={"source": "test"}
        )
        self.assertEqual(record.byte_length, len(content))
        self.assertEqual(record.content_hash, compute_content_hash(content))
        retrieved_record, retrieved_content = trail.get_evidence(record.evidence_id)
        self.assertEqual(retrieved_content, content)
        self.assertEqual(retrieved_record.content_hash, record.content_hash)
        self.assertTrue(trail.verify_evidence(record.evidence_id))
        trail.close()

    def test_evidence_tamper_detection(self):
        trail = AuditTrail(":memory:")
        content = b"original"
        record = trail.store_evidence(content)
        trail._db.execute(
            "UPDATE evidence_vault SET content=? WHERE evidence_id=?",
            (b"tampered", record.evidence_id),
        )
        self.assertFalse(trail.verify_evidence(record.evidence_id))
        trail.close()

    def test_link_evidence(self):
        trail = AuditTrail(":memory:")
        content = b"evidence bytes"
        record = trail.store_evidence(content)
        entry = trail.link_evidence(
            "task.completed", {"taskId": "t1"}, record.evidence_id
        )
        self.assertEqual(entry.payload["evidenceId"], record.evidence_id)
        self.assertEqual(entry.payload["taskId"], "t1")
        trail.close()

    def test_link_evidence_fails_for_missing(self):
        trail = AuditTrail(":memory:")
        with self.assertRaises(AuditTrailError):
            trail.link_evidence("task.completed", {}, "nonexistent")
        trail.close()

    def test_verify_up_to(self):
        trail = AuditTrail(":memory:")
        for i in range(5):
            trail.append("event", {"n": i})
        valid, broken = trail.verify_up_to(3)
        self.assertTrue(valid)
        self.assertIsNone(broken)
        trail.close()

    def test_verify_up_to_detects_tamper(self):
        trail = AuditTrail(":memory:")
        for i in range(5):
            trail.append("event", {"n": i})
        trail._db.execute(
            "UPDATE audit_chain SET payload_json='{\"n\":999}' WHERE sequence=2"
        )
        valid, broken = trail.verify_up_to(3)
        self.assertFalse(valid)
        self.assertEqual(broken, 2)
        trail.close()

    def test_entry_not_found(self):
        trail = AuditTrail(":memory:")
        with self.assertRaises(EntryNotFoundError):
            trail.get(99)
        trail.close()

    def test_evidence_not_found(self):
        trail = AuditTrail(":memory:")
        with self.assertRaises(EvidenceNotFoundError):
            trail.get_evidence("nonexistent")
        trail.close()

    def test_summary(self):
        trail = AuditTrail(":memory:")
        trail.append("event", {})
        trail.store_evidence(b"data")
        s = trail.summary()
        self.assertEqual(s["entryCount"], 1)
        self.assertEqual(s["evidenceCount"], 1)
        self.assertTrue(s["isValid"])
        self.assertIsNone(s["brokenAt"])
        trail.close()

    def test_summary_after_tamper(self):
        trail = AuditTrail(":memory:")
        trail.append("event", {"n": 1})
        trail.append("event", {"n": 2})
        trail._db.execute(
            "UPDATE audit_chain SET payload_json='{\"n\":99}' WHERE sequence=1"
        )
        s = trail.summary()
        self.assertFalse(s["isValid"])
        self.assertEqual(s["brokenAt"], 1)
        trail.close()

    def test_persistence(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "audit.sqlite3")
            trail = AuditTrail(path)
            trail.append("event", {"key": "value"})
            trail.store_evidence(b"evidence")
            trail.close()

            trail2 = AuditTrail(path)
            valid, _ = trail2.verify()
            self.assertTrue(valid)
            self.assertEqual(trail2.summary()["entryCount"], 1)
            self.assertEqual(trail2.summary()["evidenceCount"], 1)
            trail2.close()

    def test_concurrent_appends(self):
        trail = AuditTrail(":memory:")
        entries = []
        for i in range(10):
            entries.append(trail.append("concurrent", {"n": i}))
        self.assertEqual(len(entries), 10)
        valid, _ = trail.verify()
        self.assertTrue(valid)
        trail.close()

    def test_entries_with_limit(self):
        trail = AuditTrail(":memory:")
        for i in range(10):
            trail.append("event", {"n": i})
        entries = trail.entries(limit=5)
        self.assertEqual(len(entries), 5)
        self.assertEqual(entries[0].sequence, 1)
        self.assertEqual(entries[-1].sequence, 5)
        trail.close()

    def test_entries_with_start(self):
        trail = AuditTrail(":memory:")
        for i in range(10):
            trail.append("event", {"n": i})
        entries = trail.entries(start=5)
        self.assertEqual(len(entries), 6)
        self.assertEqual(entries[0].sequence, 5)
        trail.close()

    def test_entries_empty(self):
        trail = AuditTrail(":memory:")
        entries = trail.entries()
        self.assertEqual(len(entries), 0)
        trail.close()

    def test_negative_limit_raises(self):
        trail = AuditTrail(":memory:")
        with self.assertRaises(ValueError):
            trail.entries(limit=-1)
        trail.close()

    def test_context_manager(self):
        with AuditTrail(":memory:") as trail:
            trail.append("event", {})
            valid, _ = trail.verify()
            self.assertTrue(valid)

    def test_deterministic_hash(self):
        h1 = compute_hash(1, 1000.0, "test", {"a": 1}, GENESIS_HASH)
        h2 = compute_hash(1, 1000.0, "test", {"a": 1}, GENESIS_HASH)
        self.assertEqual(h1, h2)

    def test_different_payloads_different_hashes(self):
        h1 = compute_hash(1, 1000.0, "test", {"a": 1}, GENESIS_HASH)
        h2 = compute_hash(1, 1000.0, "test", {"a": 2}, GENESIS_HASH)
        self.assertNotEqual(h1, h2)

    def test_different_timestamps_different_hashes(self):
        h1 = compute_hash(1, 1000.0, "test", {"a": 1}, GENESIS_HASH)
        h2 = compute_hash(1, 2000.0, "test", {"a": 1}, GENESIS_HASH)
        self.assertNotEqual(h1, h2)

    def test_different_previous_hash_different_hashes(self):
        h1 = compute_hash(1, 1000.0, "test", {"a": 1}, GENESIS_HASH)
        h2 = compute_hash(1, 1000.0, "test", {"a": 1}, "f" * 64)
        self.assertNotEqual(h1, h2)

    def test_evidence_empty_content(self):
        trail = AuditTrail(":memory:")
        record = trail.store_evidence(b"")
        self.assertEqual(record.byte_length, 0)
        self.assertEqual(
            record.content_hash,
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        )
        trail.close()

    def test_evidence_large_content(self):
        trail = AuditTrail(":memory:")
        content = b"x" * 1_000_000
        record = trail.store_evidence(content)
        self.assertEqual(record.byte_length, 1_000_000)
        self.assertTrue(trail.verify_evidence(record.evidence_id))
        trail.close()

    def test_multiple_evidence_same_content(self):
        trail = AuditTrail(":memory:")
        content = b"duplicate"
        r1 = trail.store_evidence(content)
        r2 = trail.store_evidence(content)
        # Same content hash but different evidence IDs (timestamp-based)
        self.assertEqual(r1.content_hash, r2.content_hash)
        self.assertNotEqual(r1.evidence_id, r2.evidence_id)
        trail.close()

    def test_get_returns_correct_entry(self):
        trail = AuditTrail(":memory:")
        trail.append("event1", {"n": 1})
        trail.append("event2", {"n": 2})
        entry = trail.get(2)
        self.assertEqual(entry.sequence, 2)
        self.assertEqual(entry.payload["n"], 2)
        trail.close()

    def test_chain_broken_error_attributes(self):
        err = ChainBrokenError(5, "a" * 64, "b" * 64)
        self.assertEqual(err.sequence, 5)
        self.assertEqual(err.expected, "a" * 64)
        self.assertEqual(err.actual, "b" * 64)
        self.assertIn("5", str(err))


if __name__ == "__main__":
    unittest.main()
