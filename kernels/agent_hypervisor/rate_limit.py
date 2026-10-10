"""Rate limiting for agent operations.

Provides token bucket and sliding window rate limiters to prevent
agent resource exhaustion and enforce fair usage policies.
"""
from __future__ import annotations

import math
import threading
import time
from dataclasses import dataclass, field
from typing import Any


class RateLimitError(PermissionError):
    """Rate limit exceeded."""

    def __init__(self, message: str, *, retry_after: float | None = None):
        super().__init__(message)
        self.retry_after = retry_after


@dataclass
class TokenBucket:
    """Token bucket rate limiter.

    Tokens are added at `refill_rate` tokens per second up to `capacity`.
    Each `consume` call removes `tokens` from the bucket. If insufficient
    tokens are available, the call is rejected.
    """
    capacity: float
    refill_rate: float  # tokens per second
    _tokens: float = field(default=0.0, init=False, repr=False)
    _last_refill: float = field(default=0.0, init=False, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)

    def __post_init__(self):
        if self.capacity <= 0:
            raise ValueError("Token bucket capacity must be positive")
        if self.refill_rate < 0:
            raise ValueError("Token bucket refill_rate must be non-negative")
        self._tokens = self.capacity
        self._last_refill = time.monotonic()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self.capacity, self._tokens + elapsed * self.refill_rate)
        self._last_refill = now

    def consume(self, tokens: float = 1.0, *, now: float | None = None) -> bool:
        """Try to consume tokens from the bucket.

        Returns True if tokens were consumed, False if insufficient.
        Thread-safe.
        """
        if tokens <= 0:
            raise ValueError("Tokens to consume must be positive")
        if tokens > self.capacity:
            raise RateLimitError(
                f"Requested {tokens} tokens exceeds bucket capacity {self.capacity}"
            )

        with self._lock:
            self._refill()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False

    def consume_or_raise(self, tokens: float = 1.0) -> None:
        """Consume tokens or raise RateLimitError."""
        if not self.consume(tokens):
            with self._lock:
                self._refill()
                deficit = tokens - self._tokens
                retry_after = deficit / self.refill_rate if self.refill_rate > 0 else float("inf")
            raise RateLimitError(
                f"Rate limit exceeded: need {tokens} tokens, "
                f"have {self._tokens:.2f}",
                retry_after=retry_after,
            )

    @property
    def available_tokens(self) -> float:
        with self._lock:
            self._refill()
            return self._tokens

    @property
    def retry_after_seconds(self) -> float:
        """Seconds until at least 1 token is available."""
        with self._lock:
            self._refill()
            if self._tokens >= 1.0:
                return 0.0
            deficit = 1.0 - self._tokens
            return deficit / self.refill_rate if self.refill_rate > 0 else float("inf")


@dataclass
class SlidingWindow:
    """Sliding window rate limiter.

    Tracks request timestamps in a window of `window_seconds`.
    Rejects requests that would exceed `max_requests` in the window.
    """
    max_requests: int
    window_seconds: float
    _timestamps: list[float] = field(default_factory=list, init=False, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)

    def __post_init__(self):
        if self.max_requests <= 0:
            raise ValueError("max_requests must be positive")
        if self.window_seconds <= 0:
            raise ValueError("window_seconds must be positive")

    def _prune(self, now: float) -> None:
        cutoff = now - self.window_seconds
        self._timestamps = [t for t in self._timestamps if t > cutoff]

    def allow(self, *, now: float | None = None) -> bool:
        """Check if a request is allowed under the rate limit.

        If allowed, records the request timestamp.
        Thread-safe.
        """
        if now is None:
            now = time.monotonic()

        with self._lock:
            self._prune(now)
            if len(self._timestamps) < self.max_requests:
                self._timestamps.append(now)
                return True
            return False

    def allow_or_raise(self) -> None:
        """Allow the request or raise RateLimitError."""
        if not self.allow():
            with self._lock:
                now = time.monotonic()
                self._prune(now)
                if self._timestamps:
                    retry_after = self._timestamps[0] + self.window_seconds - now
                    retry_after = max(0.0, retry_after)
                else:
                    retry_after = self.window_seconds
            raise RateLimitError(
                f"Rate limit exceeded: {self.max_requests} requests "
                f"per {self.window_seconds}s window",
                retry_after=retry_after,
            )

    @property
    def current_count(self) -> int:
        with self._lock:
            self._prune(time.monotonic())
            return len(self._timestamps)

    @property
    def remaining(self) -> int:
        return max(0, self.max_requests - self.current_count)


class RateLimiter:
    """Multi-key rate limiter supporting both token bucket and sliding window.

    Each key (e.g., agent ID, resource) gets its own rate limiter instance.
    """

    def __init__(self):
        self._buckets: dict[str, TokenBucket] = {}
        self._windows: dict[str, SlidingWindow] = {}
        self._lock = threading.Lock()

    def configure_bucket(self, key: str, *, capacity: float,
                         refill_rate: float) -> TokenBucket:
        """Configure a token bucket for a key."""
        with self._lock:
            bucket = TokenBucket(capacity=capacity, refill_rate=refill_rate)
            self._buckets[key] = bucket
            return bucket

    def configure_window(self, key: str, *, max_requests: int,
                         window_seconds: float) -> SlidingWindow:
        """Configure a sliding window for a key."""
        with self._lock:
            window = SlidingWindow(
                max_requests=max_requests,
                window_seconds=window_seconds,
            )
            self._windows[key] = window
            return window

    def check_bucket(self, key: str, tokens: float = 1.0) -> bool:
        """Check if a token bucket request is allowed."""
        with self._lock:
            bucket = self._buckets.get(key)
        if bucket is None:
            return True  # No limit configured
        return bucket.consume(tokens)

    def check_bucket_or_raise(self, key: str, tokens: float = 1.0) -> None:
        """Consume from a token bucket or raise RateLimitError."""
        with self._lock:
            bucket = self._buckets.get(key)
        if bucket is None:
            return
        bucket.consume_or_raise(tokens)

    def check_window(self, key: str) -> bool:
        """Check if a sliding window request is allowed."""
        with self._lock:
            window = self._windows.get(key)
        if window is None:
            return True  # No limit configured
        return window.allow()

    def check_window_or_raise(self, key: str) -> None:
        """Allow a sliding window request or raise RateLimitError."""
        with self._lock:
            window = self._windows.get(key)
        if window is None:
            return
        window.allow_or_raise()

    def check_all(self, key: str, *, tokens: float = 1.0) -> bool:
        """Check both bucket and window limits for a key."""
        return self.check_bucket(key, tokens) and self.check_window(key)

    def check_all_or_raise(self, key: str, *, tokens: float = 1.0) -> None:
        """Check both limits or raise RateLimitError."""
        self.check_window_or_raise(key)
        self.check_bucket_or_raise(key, tokens)

    def reset(self, key: str) -> None:
        """Remove all rate limits for a key."""
        with self._lock:
            self._buckets.pop(key, None)
            self._windows.pop(key, None)

    def reset_all(self) -> None:
        """Remove all rate limits."""
        with self._lock:
            self._buckets.clear()
            self._windows.clear()

    def get_stats(self, key: str) -> dict[str, Any]:
        """Get rate limit statistics for a key."""
        with self._lock:
            bucket = self._buckets.get(key)
            window = self._windows.get(key)
        return {
            "key": key,
            "bucket": {
                "available_tokens": bucket.available_tokens,
                "retry_after_seconds": bucket.retry_after_seconds,
            } if bucket else None,
            "window": {
                "current_count": window.current_count,
                "remaining": window.remaining,
            } if window else None,
        }
