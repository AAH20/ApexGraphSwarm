"""Virtual File System namespacing for agent isolation.

Each agent gets an isolated VFS namespace. Paths are resolved within
the namespace, preventing agents from accessing files outside their
sandbox. Mount points allow controlled sharing between namespaces.
"""
from __future__ import annotations

import fnmatch
import hashlib
import os
import threading
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any


class VFSError(PermissionError):
    """VFS access violation or namespace error."""


@dataclass(frozen=True)
class MountPoint:
    """A mount point mapping a source path into a namespace."""
    source: str  # host path or namespace-relative source
    target: str  # where it appears in the namespace
    read_only: bool = True
    max_size_bytes: int | None = None

    def __post_init__(self):
        if not self.source or not self.target:
            raise VFSError("MountPoint source and target must be non-empty")


@dataclass
class VFSNamespace:
    """An isolated filesystem namespace for an agent."""
    name: str
    root: Path
    mounts: dict[str, MountPoint] = field(default_factory=dict)
    max_total_bytes: int = 100 * 1024 * 1024  # 100 MB default
    _lock: threading.RLock = field(default_factory=threading.RLock, repr=False)

    def __post_init__(self):
        self.root = Path(self.root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def add_mount(self, mount: MountPoint) -> None:
        with self._lock:
            target = self._normalize_path(mount.target)
            self.mounts[target] = mount

    def remove_mount(self, target: str) -> None:
        with self._lock:
            target = self._normalize_path(target)
            self.mounts.pop(target, None)

    def resolve(self, path: str) -> Path:
        """Resolve a namespace-relative path to a real filesystem path.

        Raises VFSError if the path escapes the namespace.
        """
        with self._lock:
            normalized = self._normalize_path(path)
            if not normalized:
                return self.root

            # Check mounts first (longest prefix match)
            best_match: tuple[str, MountPoint] | None = None
            for mount_target, mount in self.mounts.items():
                if normalized == mount_target or normalized.startswith(mount_target + "/"):
                    if best_match is None or len(mount_target) > len(best_match[0]):
                        best_match = (mount_target, mount)

            if best_match:
                mount_target, mount = best_match
                remainder = normalized[len(mount_target):].lstrip("/")
                source = Path(mount.source)
                if remainder:
                    source = source / remainder
                resolved = source.resolve()
                # Ensure resolved path is under the mount source
                try:
                    resolved.relative_to(Path(mount.source).resolve())
                except ValueError:
                    raise VFSError(f"Path '{path}' escapes mount point '{mount_target}'")
                return resolved

            # Default: resolve under namespace root
            candidate = (self.root / normalized).resolve()
            try:
                candidate.relative_to(self.root)
            except ValueError:
                raise VFSError(f"Path '{path}' escapes namespace '{self.name}'")
            return candidate

    def _normalize_path(self, path: str) -> str:
        """Normalize a path, rejecting traversal attempts."""
        if not path:
            return ""
        # Reject null bytes
        if "\x00" in path:
            raise VFSError("Path contains null bytes")
        pure = PurePosixPath(path)
        parts = []
        for part in pure.parts:
            if part == "/":
                # Skip the root anchor; we handle it via namespace root
                continue
            if part == "..":
                if parts:
                    parts.pop()
                # At root, ".." is a no-op (stays at root)
            elif part == ".":
                continue
            elif part:
                parts.append(part)
        return "/".join(parts)

    def write_file(self, path: str, data: bytes) -> None:
        """Write data to a file in the namespace."""
        with self._lock:
            resolved = self.resolve(path)
            # Check if this path is under a read-only mount
            normalized = self._normalize_path(path)
            for mount_target, mount in self.mounts.items():
                if normalized == mount_target or normalized.startswith(mount_target + "/"):
                    if mount.read_only:
                        raise VFSError(f"Path '{path}' is in a read-only mount")
                    if mount.max_size_bytes is not None and len(data) > mount.max_size_bytes:
                        raise VFSError(
                            f"Write of {len(data)} bytes exceeds mount limit of {mount.max_size_bytes}"
                        )
                    break

            # Check total namespace size
            if self._current_total_bytes() + len(data) > self.max_total_bytes:
                raise VFSError(
                    f"Write would exceed namespace limit of {self.max_total_bytes} bytes"
                )

            resolved.parent.mkdir(parents=True, exist_ok=True)
            resolved.write_bytes(data)

    def read_file(self, path: str) -> bytes:
        """Read data from a file in the namespace."""
        with self._lock:
            resolved = self.resolve(path)
            if not resolved.exists():
                raise VFSError(f"File not found: {path}")
            if not resolved.is_file():
                raise VFSError(f"Not a file: {path}")
            return resolved.read_bytes()

    def list_dir(self, path: str = "") -> list[str]:
        """List directory contents in the namespace."""
        with self._lock:
            resolved = self.resolve(path)
            if not resolved.exists():
                raise VFSError(f"Directory not found: {path}")
            if not resolved.is_dir():
                raise VFSError(f"Not a directory: {path}")
            return sorted(p.name for p in resolved.iterdir())

    def delete(self, path: str) -> None:
        """Delete a file or directory in the namespace."""
        with self._lock:
            resolved = self.resolve(path)
            if not resolved.exists():
                return
            # Check read-only mounts
            normalized = self._normalize_path(path)
            for mount_target, mount in self.mounts.items():
                if normalized == mount_target or normalized.startswith(mount_target + "/"):
                    if mount.read_only:
                        raise VFSError(f"Path '{path}' is in a read-only mount")
                    break
            if resolved.is_dir():
                import shutil
                shutil.rmtree(resolved)
            else:
                resolved.unlink()

    def exists(self, path: str) -> bool:
        try:
            resolved = self.resolve(path)
            return resolved.exists()
        except VFSError:
            return False

    def _current_total_bytes(self) -> int:
        """Calculate total bytes used in the namespace root (non-mount files)."""
        total = 0
        for dirpath, _dirnames, filenames in os.walk(self.root):
            for fname in filenames:
                fpath = os.path.join(dirpath, fname)
                try:
                    total += os.path.getsize(fpath)
                except OSError:
                    pass
        return total


class VFS:
    """Manages multiple isolated filesystem namespaces."""

    def __init__(self, base_path: str | os.PathLike[str]):
        self.base_path = Path(base_path).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._namespaces: dict[str, VFSNamespace] = {}
        self._lock = threading.RLock()

    def create_namespace(self, name: str, *,
                          max_total_bytes: int = 100 * 1024 * 1024) -> VFSNamespace:
        """Create a new isolated namespace."""
        with self._lock:
            if name in self._namespaces:
                raise VFSError(f"Namespace '{name}' already exists")
            if not name or "/" in name or "\x00" in name:
                raise VFSError("Invalid namespace name")
            ns = VFSNamespace(
                name=name,
                root=self.base_path / name,
                max_total_bytes=max_total_bytes,
            )
            self._namespaces[name] = ns
            return ns

    def get_namespace(self, name: str) -> VFSNamespace:
        """Get an existing namespace."""
        with self._lock:
            if name not in self._namespaces:
                raise VFSError(f"Namespace '{name}' not found")
            return self._namespaces[name]

    def destroy_namespace(self, name: str) -> None:
        """Destroy a namespace and all its contents."""
        with self._lock:
            ns = self._namespaces.pop(name, None)
            if ns is None:
                raise VFSError(f"Namespace '{name}' not found")
            import shutil
            if ns.root.exists():
                shutil.rmtree(ns.root)

    def list_namespaces(self) -> list[str]:
        """List all namespace names."""
        with self._lock:
            return sorted(self._namespaces.keys())

    def namespace_exists(self, name: str) -> bool:
        with self._lock:
            return name in self._namespaces
