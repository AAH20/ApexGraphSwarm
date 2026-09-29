"""Agent hypervisor: execution rings, VFS namespacing, DID identity, saga transactions, rate limiting.

Zero-dependency Python 3.10+ implementation.
"""
from __future__ import annotations

from .rings import Ring, RingError, RingPolicy, RingTransition
from .vfs import VFS, VFSError, VFSNamespace, MountPoint
from .identity import DID, DIDError, DIDDocument, DIDResolver
from .saga import Saga, SagaError, SagaStep, SagaState, SagaLog
from .rate_limit import RateLimiter, RateLimitError, TokenBucket, SlidingWindow

__all__ = [
    "Ring", "RingError", "RingPolicy", "RingTransition",
    "VFS", "VFSError", "VFSNamespace", "MountPoint",
    "DID", "DIDError", "DIDDocument", "DIDResolver",
    "Saga", "SagaError", "SagaStep", "SagaState", "SagaLog",
    "RateLimiter", "RateLimitError", "TokenBucket", "SlidingWindow",
]
