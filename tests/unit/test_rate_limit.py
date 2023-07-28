"""Test for prawcore.Sessions module."""
from copy import copy

from mock import patch

from prawcore.rate_limit import RateLimiter

from . import UnitTest


class TestRateLimiter(UnitTest):
    def _headers(self, remaining, used, reset):
        return {
            "x-ratelimit-remaining": str(float(remaining)),
            "x-ratelimit-used": str(used),
            "x-ratelimit-reset": str(reset),
        }

    def setup(self):
        self.rate_limiter = RateLimiter()
        self.rate_limiter.next_request_timestamp = 100

    @patch("time.sleep")
    @patch("time.time")
    def test_delay(self, mock_time, mock_sleep):
        mock_time.return_value = 1
        self.rate_limiter.delay()
        assert mock_time.called
        mock_sleep.assert_called_with(99)

    @patch("time.sleep")
    @patch("time.time")
    def test_delay__no_sleep_when_time_in_past(self, mock_time, mock_sleep):
        mock_time.return_value = 101
        self.rate_limiter.delay()
        assert mock_time.called
        assert not mock_sleep.called

    @patch("time.sleep")
    def test_delay__no_sleep_when_time_is_not_set(self, mock_sleep):
        self.rate_limiter.delay()
        assert not mock_sleep.called

    @patch("time.sleep")
    @patch("time.time")
    def test_delay__no_sleep_when_times_match(self, mock_time, mock_sleep):
        mock_time.return_value = 100
        self.rate_limiter.delay()
        assert mock_time.called
        assert not mock_sleep.called

    @patch("time.time")
    def test_update__delay_full_time_with_negative_remaining(self, mock_time):
        mock_time.return_value = 37
        self.rate_limiter.remaining = -1
        self.rate_limiter.update(self._headers(0, 100, 13))
        assert self.rate_limiter.remaining == 0
        assert self.rate_limiter.used == 100
        assert self.rate_limiter.next_request_timestamp == 50

    @patch("time.time")
    def test_update__delay_full_time_with_zero_remaining(self, mock_time):
        mock_time.return_value = 37
        self.rate_limiter.remaining = 0
        self.rate_limiter.update(self._headers(0, 100, 13))
        assert self.rate_limiter.remaining == 0
        assert self.rate_limiter.used == 100
        assert self.rate_limiter.next_request_timestamp == 50

    @patch("time.time")
    def test_update__compute_delay_with_no_previous_info(self, mock_time):
        mock_time.return_value = 100
        self.rate_limiter.update(self._headers(60, 100, 60))
        assert self.rate_limiter.remaining == 60
        assert self.rate_limiter.used == 100
        assert self.rate_limiter.next_request_timestamp == 100

    @patch("time.time")
    def test_update__compute_delay_with_single_client(self, mock_time):
        self.rate_limiter.remaining = 61
        mock_time.return_value = 100
        self.rate_limiter.update(self._headers(50, 100, 60))
        assert self.rate_limiter.remaining == 50
        assert self.rate_limiter.used == 100
        assert self.rate_limiter.next_request_timestamp == 106.66666666666667

    @patch("time.time")
    def test_update__compute_delay_with_six_clients(self, mock_time):
        self.rate_limiter.remaining = 66
        mock_time.return_value = 100
        self.rate_limiter.update(self._headers(60, 100, 72))
        assert self.rate_limiter.remaining == 60
        assert self.rate_limiter.used == 100
        assert self.rate_limiter.next_request_timestamp == 107.5

    @patch("time.time")
    def test_update__compute_delay_with_window_set(self, mock_time):
        self.rate_limiter.window_size = 600
        mock_time.return_value = 100
        self.rate_limiter.update(self._headers(599, 1, 600))
        assert self.rate_limiter.remaining == 599
        assert self.rate_limiter.used == 1
        assert self.rate_limiter.next_request_timestamp == 101

    def test_update__no_change_without_headers(self):
        prev = copy(self.rate_limiter)
        self.rate_limiter.update({})
        assert prev.remaining == self.rate_limiter.remaining
        assert prev.used == self.rate_limiter.used
        assert self.rate_limiter.next_request_timestamp == prev.next_request_timestamp

    def test_update__values_change_without_headers(self):
        self.rate_limiter.remaining = 10
        self.rate_limiter.used = 99
        self.rate_limiter.update({})
        assert self.rate_limiter.remaining == 9
        assert self.rate_limiter.used == 100
