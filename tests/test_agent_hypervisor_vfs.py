"""Tests for VFS namespacing."""
import tempfile
import unittest
from pathlib import Path

from kernels.agent_hypervisor.vfs import (
    MountPoint, VFS, VFSError, VFSNamespace,
)


class MountPointTests(unittest.TestCase):
    def test_valid_mount_point(self):
        m = MountPoint(source="/tmp", target="/mnt", read_only=True)
        self.assertEqual(m.source, "/tmp")
        self.assertEqual(m.target, "/mnt")
        self.assertTrue(m.read_only)

    def test_empty_source_rejected(self):
        with self.assertRaises(VFSError):
            MountPoint(source="", target="/mnt")

    def test_empty_target_rejected(self):
        with self.assertRaises(VFSError):
            MountPoint(source="/tmp", target="")


class VFSNamespaceTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_create_namespace(self):
        ns = VFSNamespace(name="test", root=self.root / "test")
        self.assertEqual(ns.name, "test")
        self.assertTrue(ns.root.exists())

    def test_write_and_read_file(self):
        ns = VFSNamespace(name="test", root=self.root / "test")
        ns.write_file("/hello.txt", b"world")
        self.assertEqual(ns.read_file("/hello.txt"), b"world")

    def test_path_traversal_rejected(self):
        ns = VFSNamespace(name="test", root=self.root / "test")
        # ".." at root is a no-op (stays at root), not an error
        resolved = ns.resolve("../../etc/passwd")
        self.assertEqual(resolved, (self.root / "test" / "etc" / "passwd").resolve())
        # But ".." cannot escape the namespace root
        resolved2 = ns.resolve("sub/../../../etc/passwd")
        self.assertEqual(resolved2, (self.root / "test" / "etc" / "passwd").resolve())

    def test_null_bytes_rejected(self):
        ns = VFSNamespace(name="test", root=self.root / "test")
        with self.assertRaises(VFSError):
            ns._normalize_path("file\x00.txt")

    def test_list_dir(self):
        ns = VFSNamespace(name="test", root=self.root / "test")
        ns.write_file("/a.txt", b"a")
        ns.write_file("/b.txt", b"b")
        ns.write_file("/sub/c.txt", b"c")
        entries = ns.list_dir("/")
        self.assertIn("a.txt", entries)
        self.assertIn("b.txt", entries)
        self.assertIn("sub", entries)

    def test_delete_file(self):
        ns = VFSNamespace(name="test", root=self.root / "test")
        ns.write_file("/delete-me.txt", b"bye")
        self.assertTrue(ns.exists("/delete-me.txt"))
        ns.delete("/delete-me.txt")
        self.assertFalse(ns.exists("/delete-me.txt"))

    def test_delete_directory(self):
        ns = VFSNamespace(name="test", root=self.root / "test")
        ns.write_file("/dir/file.txt", b"data")
        ns.delete("/dir")
        self.assertFalse(ns.exists("/dir"))

    def test_read_nonexistent_file(self):
        ns = VFSNamespace(name="test", root=self.root / "test")
        with self.assertRaises(VFSError):
            ns.read_file("/nonexistent.txt")

    def test_exists(self):
        ns = VFSNamespace(name="test", root=self.root / "test")
        self.assertFalse(ns.exists("/nope"))
        ns.write_file("/yes.txt", b"yes")
        self.assertTrue(ns.exists("/yes.txt"))

    def test_read_only_mount(self):
        ns = VFSNamespace(name="test", root=self.root / "test")
        # Create a real directory to mount
        source_dir = self.root / "source"
        source_dir.mkdir()
        (source_dir / "file.txt").write_text("data")

        mount = MountPoint(source=str(source_dir), target="/mnt", read_only=True)
        ns.add_mount(mount)

        # Reading should work
        data = ns.read_file("/mnt/file.txt")
        self.assertEqual(data, b"data")

        # Writing should fail
        with self.assertRaises(VFSError):
            ns.write_file("/mnt/new.txt", b"new")

    def test_writable_mount(self):
        ns = VFSNamespace(name="test", root=self.root / "test")
        source_dir = self.root / "source"
        source_dir.mkdir()

        mount = MountPoint(source=str(source_dir), target="/mnt", read_only=False)
        ns.add_mount(mount)

        ns.write_file("/mnt/new.txt", b"new")
        self.assertTrue((source_dir / "new.txt").exists())

    def test_mount_size_limit(self):
        ns = VFSNamespace(name="test", root=self.root / "test")
        source_dir = self.root / "source"
        source_dir.mkdir()

        mount = MountPoint(
            source=str(source_dir), target="/mnt",
            read_only=False, max_size_bytes=10,
        )
        ns.add_mount(mount)

        with self.assertRaises(VFSError):
            ns.write_file("/mnt/big.txt", b"x" * 100)

    def test_namespace_total_size_limit(self):
        ns = VFSNamespace(
            name="test", root=self.root / "test",
            max_total_bytes=50,
        )
        ns.write_file("/small.txt", b"x" * 30)
        with self.assertRaises(VFSError):
            ns.write_file("/big.txt", b"x" * 100)

    def test_nested_path_resolution(self):
        ns = VFSNamespace(name="test", root=self.root / "test")
        ns.write_file("/a/b/c/deep.txt", b"deep")
        self.assertEqual(ns.read_file("/a/b/c/deep.txt"), b"deep")

    def test_dot_dot_normalization(self):
        ns = VFSNamespace(name="test", root=self.root / "test")
        ns.write_file("/a.txt", b"data")
        # "sub/../a.txt" should resolve to "a.txt"
        self.assertEqual(ns.read_file("/sub/../a.txt"), b"data")


class VFSTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_create_and_get_namespace(self):
        vfs = VFS(self.base)
        ns = vfs.create_namespace("agent1")
        self.assertEqual(ns.name, "agent1")
        self.assertTrue(vfs.namespace_exists("agent1"))

        retrieved = vfs.get_namespace("agent1")
        self.assertEqual(retrieved.name, "agent1")

    def test_duplicate_namespace_rejected(self):
        vfs = VFS(self.base)
        vfs.create_namespace("agent1")
        with self.assertRaises(VFSError):
            vfs.create_namespace("agent1")

    def test_invalid_namespace_name(self):
        vfs = VFS(self.base)
        with self.assertRaises(VFSError):
            vfs.create_namespace("")
        with self.assertRaises(VFSError):
            vfs.create_namespace("a/b")

    def test_destroy_namespace(self):
        vfs = VFS(self.base)
        ns = vfs.create_namespace("agent1")
        ns.write_file("/data.txt", b"data")
        vfs.destroy_namespace("agent1")
        self.assertFalse(vfs.namespace_exists("agent1"))

    def test_list_namespaces(self):
        vfs = VFS(self.base)
        vfs.create_namespace("b")
        vfs.create_namespace("a")
        vfs.create_namespace("c")
        self.assertEqual(vfs.list_namespaces(), ["a", "b", "c"])

    def test_isolation_between_namespaces(self):
        vfs = VFS(self.base)
        ns1 = vfs.create_namespace("agent1")
        ns2 = vfs.create_namespace("agent2")
        ns1.write_file("/secret.txt", b"secret")
        self.assertTrue(ns1.exists("/secret.txt"))
        self.assertFalse(ns2.exists("/secret.txt"))

    def test_get_nonexistent_namespace(self):
        vfs = VFS(self.base)
        with self.assertRaises(VFSError):
            vfs.get_namespace("nonexistent")


if __name__ == "__main__":
    unittest.main()
