"""Tests for HotStuff BFT consensus."""
import unittest

from kernels.consensus.hotstuff import (
    Block,
    HotStuffCluster,
    HotStuffNode,
    QuorumCertificate,
    Vote,
)


class TestBlock(unittest.TestCase):
    def test_hash_is_deterministic(self):
        b1 = Block(1, "genesis", "payload-a")
        b2 = Block(1, "genesis", "payload-a")
        self.assertEqual(b1.hash, b2.hash)

    def test_hash_differs_for_different_payloads(self):
        b1 = Block(1, "genesis", "payload-a")
        b2 = Block(1, "genesis", "payload-b")
        self.assertNotEqual(b1.hash, b2.hash)

    def test_hash_differs_for_different_views(self):
        b1 = Block(1, "genesis", "payload")
        b2 = Block(2, "genesis", "payload")
        self.assertNotEqual(b1.hash, b2.hash)


class TestQuorumCertificate(unittest.TestCase):
    def test_has_quorum_with_exact_threshold(self):
        qc = QuorumCertificate("abc", 1, tuple(f"node-{i}" for i in range(3)))
        self.assertTrue(qc.has_quorum(4))

    def test_has_quorum_with_more_than_threshold(self):
        qc = QuorumCertificate("abc", 1, tuple(f"node-{i}" for i in range(4)))
        self.assertTrue(qc.has_quorum(4))

    def test_no_quorum_below_threshold(self):
        qc = QuorumCertificate("abc", 1, ("node-0", "node-1"))
        self.assertFalse(qc.has_quorum(4))


class TestHotStuffNode(unittest.TestCase):
    def test_quorum_size(self):
        node = HotStuffNode("node-0", 4, 1)
        self.assertEqual(node.quorum(), 3)

    def test_quorum_size_7_2(self):
        node = HotStuffNode("node-0", 7, 2)
        self.assertEqual(node.quorum(), 5)

    def test_create_block_with_genesis_parent(self):
        node = HotStuffNode("node-0", 4, 1)
        block = node.create_block("tx1")
        self.assertEqual(block.parent, "genesis")
        self.assertEqual(block.view, 0)
        self.assertEqual(block.payload, "tx1")

    def test_create_block_with_high_qc_parent(self):
        node = HotStuffNode("node-0", 4, 1)
        node.high_qc = QuorumCertificate("parent-hash", 0)
        block = node.create_block("tx2")
        self.assertEqual(block.parent, "parent-hash")

    def test_vote_and_collect_qc(self):
        node = HotStuffNode("node-0", 4, 1)
        block = Block(0, "genesis", "tx")
        qc = None
        for i in range(3):
            node.vote(block, "prepare")
            qc = node.collect_qc(block.hash, 0)
        self.assertIsNotNone(qc)
        assert qc is not None
        self.assertEqual(len(qc.signers), 3)

    def test_collect_qc_returns_none_below_quorum(self):
        node = HotStuffNode("node-0", 4, 1)
        block = Block(0, "genesis", "tx")
        v = Vote(block.hash, 0, "node-0", "prepare")
        qc = node.collect_qc(block.hash, 0)
        self.assertIsNone(qc)

    def test_update_high_qc(self):
        node = HotStuffNode("node-0", 4, 1)
        qc1 = QuorumCertificate("hash-1", 1)
        qc2 = QuorumCertificate("hash-2", 2)
        node.update_high_qc(qc1)
        assert node.high_qc is not None
        self.assertEqual(node.high_qc.block_hash, "hash-1")
        node.update_high_qc(qc2)
        assert node.high_qc is not None
        self.assertEqual(node.high_qc.block_hash, "hash-2")

    def test_update_high_qc_ignores_lower_view(self):
        node = HotStuffNode("node-0", 4, 1)
        qc1 = QuorumCertificate("hash-1", 2)
        qc2 = QuorumCertificate("hash-2", 1)
        node.update_high_qc(qc1)
        node.update_high_qc(qc2)
        assert node.high_qc is not None
        self.assertEqual(node.high_qc.block_hash, "hash-1")

    def test_commit_3chain_returns_none_for_short_chain(self):
        node = HotStuffNode("node-0", 4, 1)
        b0 = Block(0, "genesis", "tx0")
        b1 = Block(1, b0.hash, "tx1")
        node.blocks[b0.hash] = b0
        node.blocks[b1.hash] = b1
        self.assertIsNone(node.commit_3chain(b1))

    def test_commit_3chain_returns_grandparent(self):
        node = HotStuffNode("node-0", 4, 1)
        b0 = Block(0, "genesis", "tx0")
        b1 = Block(1, b0.hash, "tx1")
        b2 = Block(2, b1.hash, "tx2")
        node.blocks[b0.hash] = b0
        node.blocks[b1.hash] = b1
        node.blocks[b2.hash] = b2
        committed = node.commit_3chain(b2)
        self.assertIsNotNone(committed)
        assert committed is not None
        self.assertEqual(committed.hash, b0.hash)


class TestHotStuffCluster(unittest.TestCase):
    def test_invalid_parameters(self):
        with self.assertRaises(ValueError):
            HotStuffCluster(n=3, f=1)

    def test_valid_parameters(self):
        cluster = HotStuffCluster(n=4, f=1)
        self.assertEqual(cluster.n, 4)
        self.assertEqual(cluster.f, 1)

    def test_leader_rotation(self):
        cluster = HotStuffCluster(n=4, f=1)
        self.assertEqual(cluster.leader.node_id, "node-0")
        cluster.rotate_leader()
        self.assertEqual(cluster.leader.node_id, "node-1")
        cluster.rotate_leader()
        cluster.rotate_leader()
        cluster.rotate_leader()
        self.assertEqual(cluster.leader.node_id, "node-0")

    def test_run_view_returns_none_for_first_two_views(self):
        cluster = HotStuffCluster(n=4, f=1)
        result = cluster.run_view("tx1")
        self.assertIsNone(result)

    def test_run_view_commits_after_3_views(self):
        cluster = HotStuffCluster(n=4, f=1)
        cluster.run_view("tx1")
        cluster.run_view("tx2")
        result = cluster.run_view("tx3")
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.payload, "tx1")

    def test_run_views_commits_correct_blocks(self):
        cluster = HotStuffCluster(n=4, f=1)
        committed = cluster.run_views(["tx1", "tx2", "tx3", "tx4", "tx5"])
        self.assertEqual(len(committed), 3)
        self.assertEqual(committed[0].payload, "tx1")
        self.assertEqual(committed[1].payload, "tx2")
        self.assertEqual(committed[2].payload, "tx3")

    def test_committed_blocks_form_chain(self):
        cluster = HotStuffCluster(n=4, f=1)
        committed = cluster.run_views(["tx1", "tx2", "tx3", "tx4"])
        self.assertEqual(len(committed), 2)
        self.assertEqual(committed[1].parent, committed[0].hash)

    def test_all_nodes_vote_in_each_phase(self):
        cluster = HotStuffCluster(n=4, f=1)
        cluster.run_view("tx1")
        for node in cluster.nodes:
            # Each node votes once per phase (prepare, pre-commit, commit)
            vote_count = sum(len(v) for v in node.votes.values())
            self.assertEqual(vote_count, 3)

    def test_high_qc_updates_after_view(self):
        cluster = HotStuffCluster(n=4, f=1)
        cluster.run_view("tx1")
        leader = cluster.nodes[0]
        self.assertIsNotNone(leader.high_qc)


if __name__ == "__main__":
    unittest.main()
