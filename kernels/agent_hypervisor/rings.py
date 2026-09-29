"""Execution rings: privilege levels for agent isolation.

Ring 0: Kernel/hypervisor (highest privilege)
Ring 1: System services (trusted infrastructure)
Ring 2: Agent runtime (sandboxed agents)
Ring 3: Untrusted user code (lowest privilege)

Lower ring numbers = higher privilege. Agents in ring N can only call
into ring N-1 (more privileged) through controlled gates, never the
reverse.
"""
from __future__ import annotations

import enum
import functools
import threading
from dataclasses import dataclass, field
from typing import Any, Callable


class RingError(PermissionError):
    """Ring transition or capability violation."""


class Ring(enum.IntEnum):
    KERNEL = 0
    SYSTEM = 1
    AGENT = 2
    USER = 3

    @property
    def name(self) -> str:
        return _RING_NAMES[self]


_RING_NAMES = {
    Ring.KERNEL: "kernel",
    Ring.SYSTEM: "system",
    Ring.AGENT: "agent",
    Ring.USER: "user",
}


@dataclass(frozen=True)
class RingTransition:
    """A controlled transition from one ring to another."""
    source: Ring
    target: Ring
    gate: str  # identifier for the controlled entry point

    def validate(self) -> None:
        """Ensure the transition is legal (only to more-privileged rings)."""
        if self.target >= self.source:
            raise RingError(
                f"Invalid ring transition: {self.source.name} -> {self.target.name}. "
                f"Can only transition to more-privileged rings (lower numbers)."
            )


@dataclass
class RingPolicy:
    """Defines allowed ring transitions and capabilities."""
    allowed_transitions: dict[Ring, set[Ring]] = field(default_factory=dict)
    capabilities: dict[Ring, set[str]] = field(default_factory=dict)

    def __post_init__(self):
        if not self.allowed_transitions:
            self.allowed_transitions = {
                Ring.USER: {Ring.AGENT, Ring.SYSTEM, Ring.KERNEL},
                Ring.AGENT: {Ring.SYSTEM, Ring.KERNEL},
                Ring.SYSTEM: {Ring.KERNEL},
                Ring.KERNEL: set(),
            }
        if not self.capabilities:
            self.capabilities = {
                Ring.KERNEL: {"*"},
                Ring.SYSTEM: {"fs.read", "fs.write", "net.connect", "process.spawn"},
                Ring.AGENT: {"fs.read", "fs.write", "net.connect"},
                Ring.USER: {"fs.read"},
            }

    def can_transition(self, source: Ring, target: Ring) -> bool:
        return target in self.allowed_transitions.get(source, set())

    def has_capability(self, ring: Ring, capability: str) -> bool:
        caps = self.capabilities.get(ring, set())
        return "*" in caps or capability in caps


class RingContext:
    """Thread-local ring context for the current execution."""

    _local = threading.local()

    @classmethod
    def current(cls) -> Ring:
        return getattr(cls._local, "ring", Ring.KERNEL)

    @classmethod
    def set(cls, ring: Ring) -> None:
        cls._local.ring = ring

    @classmethod
    def reset(cls) -> None:
        cls._local.ring = Ring.KERNEL

    def __init__(self, ring: Ring):
        self.ring = ring
        self._previous: Ring | None = None

    def __enter__(self):
        self._previous = self.current()
        self.set(self.ring)
        return self

    def __exit__(self, *exc):
        if self._previous is not None:
            self.set(self._previous)
        return False


def require_ring(target: Ring, policy: RingPolicy | None = None):
    """Decorator: require execution in a specific ring or more privileged."""
    policy = policy or RingPolicy()

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            current = RingContext.current()
            if current > target:
                raise RingError(
                    f"Ring violation: {fn.__name__} requires ring {target.name} "
                    f"or higher, but current ring is {current.name}"
                )
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def transition_gate(source: Ring, target: Ring, gate_name: str,
                     policy: RingPolicy | None = None):
    """Create a controlled transition gate between rings."""
    policy = policy or RingPolicy()
    transition = RingTransition(source=source, target=target, gate=gate_name)
    transition.validate()
    if not policy.can_transition(source, target):
        raise RingError(
            f"Ring transition {source.name} -> {target.name} not allowed by policy"
        )
    return transition
