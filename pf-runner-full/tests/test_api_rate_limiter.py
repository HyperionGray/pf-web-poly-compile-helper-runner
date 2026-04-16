"""Tests for the API rate limiter in pf_api.py."""

import sys
import time
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pf_api import _SlidingWindowRateLimiter


class TestSlidingWindowRateLimiter(unittest.TestCase):
    def test_allows_requests_within_limit(self):
        limiter = _SlidingWindowRateLimiter(max_requests=5, window_seconds=60)
        for _ in range(5):
            self.assertTrue(limiter.is_allowed("client1"))

    def test_blocks_request_over_limit(self):
        limiter = _SlidingWindowRateLimiter(max_requests=3, window_seconds=60)
        for _ in range(3):
            limiter.is_allowed("client1")
        self.assertFalse(limiter.is_allowed("client1"))

    def test_different_clients_tracked_independently(self):
        limiter = _SlidingWindowRateLimiter(max_requests=2, window_seconds=60)
        limiter.is_allowed("clientA")
        limiter.is_allowed("clientA")
        # clientA is now at limit
        self.assertFalse(limiter.is_allowed("clientA"))
        # clientB is unaffected
        self.assertTrue(limiter.is_allowed("clientB"))

    def test_window_expiry_allows_new_requests(self):
        limiter = _SlidingWindowRateLimiter(max_requests=2, window_seconds=1)
        limiter.is_allowed("client1")
        limiter.is_allowed("client1")
        self.assertFalse(limiter.is_allowed("client1"))
        # Wait for window to expire
        time.sleep(1.1)
        self.assertTrue(limiter.is_allowed("client1"))

    def test_zero_limit_blocks_all(self):
        limiter = _SlidingWindowRateLimiter(max_requests=0, window_seconds=60)
        self.assertFalse(limiter.is_allowed("client1"))

    def test_large_limit_allows_many(self):
        limiter = _SlidingWindowRateLimiter(max_requests=1000, window_seconds=60)
        for _ in range(999):
            self.assertTrue(limiter.is_allowed("client1"))


if __name__ == "__main__":
    unittest.main()
