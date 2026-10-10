"""Tests for rate limiting."""
import time
import unittest

from kernels.agent_hypervisor.rate_limit import (
    RateLimiter, RateLimitError, SlidingWindow, TokenBucket,
)


class TokenBucketTests(unittest.TestCase):
    def test_creation(self):
        bucket = TokenBucket(capacity=10, refill_rate=1.0)
        self.assertEqual(bucket.capacity, 10)
        self.assertEqual(bucket.refill_rate, 1.0)

    def test_invalid_capacity(self):
        with self.assertRaises(ValueError):
            TokenBucket(capacity=0, refill_rate=1.0)
        with self.assertRaises(ValueError):
            TokenBucket(capacity=-1, refill_rate=1.0)

    def test_invalid_refill_rate(self):
        with self.assertRaises(ValueError):
            TokenBucket(capacity=10, refill_rate=-1)

    def test_initial_tokens_equal_capacity(self):
        bucket = TokenBucket(capacity=5, refill_rate=1.0)
        self.assertEqual(bucket.available_tokens, 5.0)

    def test_consume_reduces_tokens(self):
        bucket = TokenBucket(capacity=10, refill_rate=0.0)
        self.assertTrue(bucket.consume(3.0))
        self.assertEqual(bucket.available_tokens, 7.0)

    def test_consume_fails_when_insufficient(self):
        bucket = TokenBucket(capacity=5, refill_rate=0.0)
        # Consuming more than capacity raises RateLimitError
        with self.assertRaises(RateLimitError):
            bucket.consume(6.0)
        # Tokens should not be consumed
        self.assertEqual(bucket.available_tokens, 5.0)
        # Consuming within capacity but more than available returns False
        bucket2 = TokenBucket(capacity=10, refill_rate=0.0)
        bucket2.consume(8.0)
        self.assertFalse(bucket2.consume(3.0))
        self.assertEqual(bucket2.available_tokens, 2.0)

    def test_consume_exact_amount(self):
        bucket = TokenBucket(capacity=5, refill_rate=0.0)
        self.assertTrue(bucket.consume(5.0))
        self.assertEqual(bucket.available_tokens, 0.0)

    def test_consume_zero_rejected(self):
        bucket = TokenBucket(capacity=5, refill_rate=1.0)
        with self.assertRaises(ValueError):
            bucket.consume(0)

    def test_consume_negative_rejected(self):
        bucket = TokenBucket(capacity=5, refill_rate=1.0)
        with self.assertRaises(ValueError):
            bucket.consume(-1)

    def test_consume_exceeding_capacity_rejected(self):
        bucket = TokenBucket(capacity=5, refill_rate=1.0)
        with self.assertRaises(RateLimitError):
            bucket.consume(6.0)

    def test_consume_or_raise_success(self):
        bucket = TokenBucket(capacity=5, refill_rate=0.0)
        bucket.consume_or_raise(3.0)  # Should not raise
        self.assertEqual(bucket.available_tokens, 2.0)

    def test_consume_or_raise_failure(self):
        bucket = TokenBucket(capacity=5, refill_rate=0.0)
        # Consuming more than capacity raises RateLimitError
        with self.assertRaises(RateLimitError):
            bucket.consume_or_raise(6.0)
        # Consuming within capacity but more than available raises with retry_after
        bucket2 = TokenBucket(capacity=10, refill_rate=1.0)
        bucket2.consume(8.0)
        with self.assertRaises(RateLimitError) as ctx:
            bucket2.consume_or_raise(5.0)
        self.assertIsNotNone(ctx.exception.retry_after)
        self.assertGreater(ctx.exception.retry_after, 0)

    def test_refill_over_time(self):
        bucket = TokenBucket(capacity=10, refill_rate=100.0)
        bucket.consume(5.0)
        # Allow small tolerance for refill during consume
        self.assertAlmostEqual(bucket.available_tokens, 5.0, places=1)
        time.sleep(0.1)  # Should refill ~10 tokens
        self.assertGreater(bucket.available_tokens, 5.0)

    def test_retry_after_seconds(self):
        bucket = TokenBucket(capacity=5, refill_rate=1.0)
        self.assertEqual(bucket.retry_after_seconds, 0.0)
        bucket.consume(5.0)
        self.assertGreater(bucket.retry_after_seconds, 0.0)


class SlidingWindowTests(unittest.TestCase):
    def test_creation(self):
        window = SlidingWindow(max_requests=5, window_seconds=60.0)
        self.assertEqual(window.max_requests, 5)
        self.assertEqual(window.window_seconds, 60.0)

    def test_invalid_max_requests(self):
        with self.assertRaises(ValueError):
            SlidingWindow(max_requests=0, window_seconds=60.0)

    def test_invalid_window_seconds(self):
        with self.assertRaises(ValueError):
            SlidingWindow(max_requests=5, window_seconds=0)

    def test_allow_within_limit(self):
        window = SlidingWindow(max_requests=3, window_seconds=60.0)
        self.assertTrue(window.allow())
        self.assertTrue(window.allow())
        self.assertTrue(window.allow())
        self.assertEqual(window.current_count, 3)

    def test_reject_over_limit(self):
        window = SlidingWindow(max_requests=2, window_seconds=60.0)
        self.assertTrue(window.allow())
        self.assertTrue(window.allow())
        self.assertFalse(window.allow())

    def test_remaining(self):
        window = SlidingWindow(max_requests=5, window_seconds=60.0)
        self.assertEqual(window.remaining, 5)
        window.allow()
        self.assertEqual(window.remaining, 4)

    def test_window_expires(self):
        window = SlidingWindow(max_requests=1, window_seconds=0.05)
        self.assertTrue(window.allow())
        self.assertFalse(window.allow())
        time.sleep(0.06)
        self.assertTrue(window.allow())  # Old request expired

    def test_allow_or_raise_success(self):
        window = SlidingWindow(max_requests=5, window_seconds=60.0)
        window.allow_or_raise()  # Should not raise

    def test_allow_or_raise_failure(self):
        window = SlidingWindow(max_requests=1, window_seconds=60.0)
        window.allow_or_raise()
        with self.assertRaises(RateLimitError) as ctx:
            window.allow_or_raise()
        self.assertIsNotNone(ctx.exception.retry_after)
        self.assertGreater(ctx.exception.retry_after, 0)


class RateLimiterTests(unittest.TestCase):
    def test_configure_bucket(self):
        rl = RateLimiter()
        bucket = rl.configure_bucket("agent1", capacity=10, refill_rate=1.0)
        self.assertIsInstance(bucket, TokenBucket)

    def test_configure_window(self):
        rl = RateLimiter()
        window = rl.configure_window("agent1", max_requests=5, window_seconds=60.0)
        self.assertIsInstance(window, SlidingWindow)

    def test_check_bucket_no_limit_configured(self):
        rl = RateLimiter()
        self.assertTrue(rl.check_bucket("unknown-key"))

    def test_check_bucket_with_limit(self):
        rl = RateLimiter()
        rl.configure_bucket("agent1", capacity=5, refill_rate=0.0)
        self.assertTrue(rl.check_bucket("agent1", tokens=3))
        self.assertFalse(rl.check_bucket("agent1", tokens=3))

    def test_check_bucket_or_raise(self):
        rl = RateLimiter()
        rl.configure_bucket("agent1", capacity=5, refill_rate=0.0)
        rl.check_bucket_or_raise("agent1", tokens=3)
        with self.assertRaises(RateLimitError):
            rl.check_bucket_or_raise("agent1", tokens=3)

    def test_check_window_no_limit_configured(self):
        rl = RateLimiter()
        self.assertTrue(rl.check_window("unknown-key"))

    def test_check_window_with_limit(self):
        rl = RateLimiter()
        rl.configure_window("agent1", max_requests=2, window_seconds=60.0)
        self.assertTrue(rl.check_window("agent1"))
        self.assertTrue(rl.check_window("agent1"))
        self.assertFalse(rl.check_window("agent1"))

    def test_check_window_or_raise(self):
        rl = RateLimiter()
        rl.configure_window("agent1", max_requests=1, window_seconds=60.0)
        rl.check_window_or_raise("agent1")
        with self.assertRaises(RateLimitError):
            rl.check_window_or_raise("agent1")

    def test_check_all(self):
        rl = RateLimiter()
        rl.configure_bucket("agent1", capacity=10, refill_rate=0.0)
        rl.configure_window("agent1", max_requests=5, window_seconds=60.0)
        self.assertTrue(rl.check_all("agent1", tokens=3))
        self.assertFalse(rl.check_all("agent1", tokens=8))  # Bucket exhausted

    def test_check_all_or_raise(self):
        rl = RateLimiter()
        rl.configure_bucket("agent1", capacity=10, refill_rate=0.0)
        rl.configure_window("agent1", max_requests=1, window_seconds=60.0)
        rl.check_all_or_raise("agent1", tokens=1)
        with self.assertRaises(RateLimitError):
            rl.check_all_or_raise("agent1", tokens=1)  # Window exhausted

    def test_reset(self):
        rl = RateLimiter()
        rl.configure_bucket("agent1", capacity=5, refill_rate=0.0)
        rl.check_bucket("agent1", tokens=3)
        rl.reset("agent1")
        # After reset, no limit is configured
        self.assertTrue(rl.check_bucket("agent1", tokens=100))

    def test_reset_all(self):
        rl = RateLimiter()
        rl.configure_bucket("a", capacity=5, refill_rate=0.0)
        rl.configure_bucket("b", capacity=5, refill_rate=0.0)
        rl.reset_all()
        self.assertTrue(rl.check_bucket("a", tokens=100))
        self.assertTrue(rl.check_bucket("b", tokens=100))

    def test_get_stats(self):
        rl = RateLimiter()
        rl.configure_bucket("agent1", capacity=10, refill_rate=1.0)
        rl.configure_window("agent1", max_requests=5, window_seconds=60.0)
        stats = rl.get_stats("agent1")
        self.assertEqual(stats["key"], "agent1")
        self.assertIsNotNone(stats["bucket"])
        self.assertIsNotNone(stats["window"])

    def test_get_stats_no_limits(self):
        rl = RateLimiter()
        stats = rl.get_stats("unknown")
        self.assertIsNone(stats["bucket"])
        self.assertIsNone(stats["window"])


if __name__ == "__main__":
    unittest.main()
