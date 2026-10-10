import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from apexgraphswarm.repository_conflicts import (
    RepositoryConflictError,
    _stable_plan_digest,
    plan_repository_conflicts,
    verify_repository_conflict_plan,
)


class RepositoryConflictTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.repo = Path(self.temporary.name) / "repo with spaces"
        self.repo.mkdir()
        self._git("init", "-q", "-b", "base")
        self._git("config", "user.name", "Conflict Fixture")
        self._git("config", "user.email", "fixture@example.invalid")
        self._write("read this file.txt", "declared base evidence\n")
        self._write("deleted.txt", "delete me\n")
        self._write("rename source with spaces.py", "".join(f"line {i}\n" for i in range(80)))
        self._write("copy source with spaces.txt", "".join(f"copy evidence {i}\n" for i in range(100)))
        self._write("stable.txt", "base content\n")
        self._commit("base fixture")
        self.base = self._git("rev-parse", "HEAD")

    def tearDown(self):
        self.temporary.cleanup()

    def _git(self, *args, check=True, cwd=None, env=None):
        environment = os.environ.copy()
        if env:
            environment.update(env)
        result = subprocess.run(["git", "-C", str(cwd or self.repo), *args],
                                capture_output=True, check=False, env=environment,
                                timeout=5)
        if check and result.returncode:
            self.fail(f"fixture git command failed ({result.returncode}): {args!r}: "
                      f"{result.stderr.decode('utf-8', 'replace')[:500]}")
        return result.stdout.decode("utf-8", errors="strict").strip()

    def _write(self, relative, content):
        target = self.repo / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    def _commit(self, message):
        self._git("add", "-A")
        self._git("commit", "-qm", message)
        return self._git("rev-parse", "HEAD")

    def _branch_from_base(self, name):
        self._git("switch", "-q", "-c", name, self.base)

    def test_derives_rename_delete_copy_and_git_object_provenance(self):
        self._branch_from_base("candidate-a")
        (self.repo / "rename source with spaces.py").rename(self.repo / "renamed target with spaces.py")
        (self.repo / "deleted.txt").unlink()
        shutil.copyfile(self.repo / "copy source with spaces.txt",
                        self.repo / "copy destination with spaces.txt")
        head = self._commit("rename delete and copy")

        plan = plan_repository_conflicts(self.repo, self.base, [{
            "id": "candidate-a", "dependencies": [], "head_revision": head,
            "reads": ["read this file.txt"],
        }])
        task = plan["tasks"][0]
        writes = task["writes"]
        paths = {item["path"] for item in writes}
        self.assertIn("rename source with spaces.py", paths)
        self.assertIn("renamed target with spaces.py", paths)
        self.assertIn("deleted.txt", paths)
        self.assertIn("copy source with spaces.txt", paths)
        self.assertIn("copy destination with spaces.txt", paths)
        self.assertTrue(any(item["endpoint"] == "rename_from" for item in writes))
        self.assertTrue(any(item["endpoint"] == "rename_to" for item in writes))
        self.assertTrue(any(item["endpoint"] == "copy_source_conservative" for item in writes))
        deleted = next(item for item in writes if item["path"] == "deleted.txt")
        self.assertIsNotNone(deleted["beforeBlobObjectId"])
        self.assertIsNone(deleted["afterBlobObjectId"])
        self.assertEqual(task["declaredReads"][0]["path"], "read this file.txt")
        self.assertEqual(task["readEvidence"], "declared_and_verified_at_base_not_runtime_trace")
        self.assertEqual(plan["base"]["objectFormat"], "sha1")
        self.assertEqual(len(task["treeObjectId"]), 40)
        self.assertEqual(len(task["changeSha256"]), 64)
        self.assertTrue(plan["metadata"]["readOnly"])
        self.assertFalse(plan["metadata"]["changesApplied"])
        self.assertTrue(plan["metadata"]["workingTreeIgnored"])

    def test_prefix_conflicts_serialize_heads_without_losing_existing_dag(self):
        self._branch_from_base("alpha-head")
        self._write("src", "alpha adds a file at the parent path\n")
        alpha = self._commit("alpha parent file")

        self._git("switch", "-q", "base")
        self._git("switch", "-q", "-c", "beta-head", self.base)
        self._write("src/child.py", "beta adds a child path\n")
        beta = self._commit("beta child file")

        tasks = [
            {"id": "alpha", "dependencies": ["beta"], "head_revision": alpha, "reads": []},
            {"id": "beta", "dependencies": [], "head_revision": beta, "reads": []},
        ]
        plan = plan_repository_conflicts(self.repo, self.base, tasks)
        self.assertEqual(plan["waves"], [["beta"], ["alpha"]])
        self.assertEqual(len(plan["conflicts"]), 1)
        conflict = plan["conflicts"][0]
        self.assertEqual(conflict["serializedBefore"], "beta")
        self.assertEqual(conflict["serializedAfter"], "alpha")
        self.assertEqual(conflict["overlaps"], [{
            "firstPath": "src", "secondPath": "src/child.py", "reason": "write_write"}])

    def test_worktree_changes_are_ignored_and_declared_reads_are_base_verified(self):
        self._branch_from_base("candidate")
        self._write("committed.txt", "candidate change\n")
        head = self._commit("candidate commit")
        tasks = [{"id": "candidate", "head_revision": head, "reads": ["stable.txt"]}]
        clean = plan_repository_conflicts(self.repo, self.base, tasks)

        self._write("stable.txt", "uncommitted local edit\n")
        self._write("untracked local file.txt", "not part of the pinned commits\n")
        dirty = plan_repository_conflicts(self.repo, self.base, tasks)
        self.assertEqual(clean["inputDigest"], dirty["inputDigest"])
        self.assertEqual(clean["planDigest"], dirty["planDigest"])
        self.assertEqual(clean["tasks"][0]["writes"], dirty["tasks"][0]["writes"])
        self.assertEqual(dirty["tasks"][0]["declaredReads"][0]["blobObjectId"],
                         clean["tasks"][0]["declaredReads"][0]["blobObjectId"])

    def test_stale_verifier_detects_moved_refs_and_forged_semantics(self):
        self._branch_from_base("candidate")
        self._write("candidate.txt", "first head\n")
        first_head = self._commit("first candidate")
        plan = plan_repository_conflicts(self.repo, self.base, [{
            "id": "candidate", "head_revision": "candidate", "reads": []}])
        self.assertEqual(plan["tasks"][0]["resolvedCommit"], first_head)
        self.assertEqual(verify_repository_conflict_plan(self.repo, plan)["status"], "current")
        node_roundtrip = subprocess.run(
            ["node", "-e", "process.stdout.write(JSON.stringify(JSON.parse(require('fs').readFileSync(0, 'utf8'))))"],
            input=json.dumps(plan), text=True, capture_output=True, check=True, timeout=5)
        browser_plan = json.loads(node_roundtrip.stdout)
        self.assertIs(type(browser_plan["metadata"]["totalTimeLimitSeconds"]), int)
        self.assertEqual(verify_repository_conflict_plan(self.repo, browser_plan)["status"], "current")

        self._git("switch", "-q", "base")
        self._git("switch", "-q", "-c", "advance", self.base)
        self._write("candidate.txt", "moved head\n")
        second_head = self._commit("advance candidate")
        self._git("branch", "-f", "candidate", second_head)
        stale = verify_repository_conflict_plan(self.repo, plan)
        self.assertEqual(stale["status"], "stale")
        self.assertTrue(stale["stale"])
        self.assertNotEqual(stale["currentHeadCommits"]["candidate"], first_head)

        self._git("branch", "-f", "candidate", first_head)
        forged = json.loads(json.dumps(plan))
        forged["waves"] = [["forged"]]
        forged["planDigest"] = _stable_plan_digest(forged)
        semantics = verify_repository_conflict_plan(self.repo, forged)
        self.assertTrue(semantics["storedPlanDigestValid"])
        self.assertFalse(semantics["semanticPlanMatchesCurrent"])
        self.assertEqual(semantics["status"], "stale")

        forged_metadata = json.loads(json.dumps(plan))
        forged_metadata["metadata"]["readOnly"] = False
        forged_metadata["planDigest"] = _stable_plan_digest(forged_metadata)
        metadata_check = verify_repository_conflict_plan(self.repo, forged_metadata)
        self.assertFalse(metadata_check["semanticPlanMatchesCurrent"])
        self.assertEqual(metadata_check["status"], "stale")

    def test_bad_revisions_paths_dependencies_and_unmerged_index_fail_closed(self):
        with self.assertRaisesRegex(RepositoryConflictError, "revision token"):
            plan_repository_conflicts(self.repo, "--help", [{"id": "a", "head_revision": self.base}])
        with self.assertRaisesRegex(RepositoryConflictError, "revision token"):
            plan_repository_conflicts(self.repo, self.base, [{"id": "a", "head_revision": "missing ref"}])
        with self.assertRaisesRegex(RepositoryConflictError, "traversing path"):
            plan_repository_conflicts(self.repo, self.base, [{
                "id": "a", "head_revision": self.base, "reads": ["../outside"]}])
        with self.assertRaisesRegex(RepositoryConflictError, "missing from the base tree"):
            plan_repository_conflicts(self.repo, self.base, [{
                "id": "a", "head_revision": self.base, "reads": ["not-present"]}])
        with self.assertRaisesRegex(RepositoryConflictError, "missing dependencies"):
            plan_repository_conflicts(self.repo, self.base, [{
                "id": "a", "head_revision": self.base, "dependencies": ["missing"]}])

        other_head = self._git("switch", "-q", "-c", "conflicting", self.base) or None
        self._write("stable.txt", "other branch value\n")
        other_head = self._commit("other branch edit")
        self._git("switch", "-q", "base")
        self._write("stable.txt", "base branch value\n")
        local_head = self._commit("local branch edit")
        self._git("merge", "conflicting", check=False)
        self.assertNotEqual(self._git("ls-files", "--unmerged", "-z"), "")
        with self.assertRaisesRegex(RepositoryConflictError, "Unmerged index"):
            plan_repository_conflicts(self.repo, self.base, [{
                "id": "a", "head_revision": other_head}, {"id": "b", "head_revision": local_head}])


if __name__ == "__main__":
    unittest.main()
