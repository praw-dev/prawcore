"""Test for prawcore.Sessions module."""

from copy import copy
from unittest.mock import patch

import pytest

from prawcore.const import NANOSECONDS
from prawcore.rate_limit import RateLimiter

from . import UnitTest


class TestRateLimiter(UnitTest):
    @pytest.fixture
    def rate_limiter(self):
        rate_limiter = RateLimiter(window_size=600)
        rate_limiter.next_request_timestamp_ns = 100 * NANOSECONDS
        return rate_limiter

    @staticmethod
    def _headers(remaining, used, reset):
        return {
            "x-ratelimit-remaining": str(float(remaining)),
            "x-ratelimit-used": str(used),
            "x-ratelimit-reset": str(reset),
        }

    @patch("time.monotonic_ns")
    @patch("time.sleep")
    def test_delay(self, mock_sleep, mock_monotonic_ns, rate_limiter):
        mock_monotonic_ns.return_value = 1 * NANOSECONDS
        rate_limiter.delay()
        assert mock_monotonic_ns.called
        mock_sleep.assert_called_with(99)

    @patch("time.monotonic_ns")
    @patch("time.sleep")
    def test_delay__no_sleep_when_time_in_past(self, mock_sleep, mock_monotonic_ns, rate_limiter):
        mock_monotonic_ns.return_value = 101 * NANOSECONDS
        rate_limiter.delay()
        assert mock_monotonic_ns.called
        assert not mock_sleep.called

    @patch("time.sleep")
    def test_delay__no_sleep_when_time_is_not_set(self, mock_sleep, rate_limiter):
        rate_limiter.next_request_timestamp_ns = None
        rate_limiter.delay()
        assert not mock_sleep.called

    @patch("time.monotonic_ns")
    @patch("time.sleep")
    def test_delay__no_sleep_when_times_match(self, mock_sleep, mock_monotonic_ns, rate_limiter):
        mock_monotonic_ns.return_value = 100 * NANOSECONDS
        rate_limiter.delay()
        assert mock_monotonic_ns.called
        assert not mock_sleep.called

    @patch("time.monotonic_ns")
    def test_update__compute_delay_with_no_previous_info(self, mock_monotonic_ns, rate_limiter):
        mock_monotonic_ns.return_value = 100 * NANOSECONDS
        rate_limiter.update(self._headers(60, 100, 60))
        assert rate_limiter.remaining == 60
        assert rate_limiter.used == 100
        assert rate_limiter.next_request_timestamp_ns == 100 * NANOSECONDS

    @patch("time.monotonic_ns")
    def test_update__compute_delay_with_single_client(self, mock_monotonic_ns, rate_limiter):
        rate_limiter.window_size = 150
        mock_monotonic_ns.return_value = 100 * NANOSECONDS
        rate_limiter.update(self._headers(50, 100, 60))
        assert rate_limiter.remaining == 50
        assert rate_limiter.used == 100
        assert rate_limiter.next_request_timestamp_ns == 110 * NANOSECONDS

    @patch("time.monotonic_ns")
    def test_update__compute_delay_with_six_clients(self, mock_monotonic_ns, rate_limiter):
        rate_limiter.remaining = 66
        rate_limiter.window_size = 180
        mock_monotonic_ns.return_value = 100 * NANOSECONDS
        rate_limiter.update(self._headers(60, 100, 72))
        assert rate_limiter.remaining == 60
        assert rate_limiter.used == 100
        assert rate_limiter.next_request_timestamp_ns == 104.5 * NANOSECONDS

    @patch("time.monotonic_ns")
    def test_update__delay_full_time_with_negative_remaining(self, mock_monotonic_ns, rate_limiter):
        mock_monotonic_ns.return_value = 37 * NANOSECONDS
        rate_limiter.update(self._headers(0, 100, 13))
        assert rate_limiter.remaining == 0
        assert rate_limiter.used == 100
        assert rate_limiter.next_request_timestamp_ns == 50 * NANOSECONDS

    @patch("time.monotonic_ns")
    def test_update__delay_full_time_with_zero_remaining(self, mock_monotonic_ns, rate_limiter):
        mock_monotonic_ns.return_value = 37 * NANOSECONDS
        rate_limiter.update(self._headers(0, 100, 13))
        assert rate_limiter.remaining == 0
        assert rate_limiter.used == 100
        assert rate_limiter.next_request_timestamp_ns == 50 * NANOSECONDS

    @patch("time.monotonic_ns")
    def test_update__delay_full_time_with_zero_remaining_and_no_sleep_time(self, mock_monotonic_ns, rate_limiter):
        mock_monotonic_ns.return_value = 37 * NANOSECONDS
        rate_limiter.update(self._headers(0, 100, 0))
        assert rate_limiter.remaining == 0
        assert rate_limiter.used == 100
        assert rate_limiter.next_request_timestamp_ns == 38 * NANOSECONDS

    def test_update__no_change_without_headers(self, rate_limiter):
        prev = copy(rate_limiter)
        rate_limiter.update({})
        assert prev.remaining == rate_limiter.remaining
        assert prev.used == rate_limiter.used
        assert rate_limiter.next_request_timestamp_ns == prev.next_request_timestamp_ns

    def test_update__values_change_without_headers(self, rate_limiter):
        rate_limiter.remaining = 10
        rate_limiter.used = 99
        rate_limiter.update({})
        assert rate_limiter.remaining == 9
        assert rate_limiter.used == 100
