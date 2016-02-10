"""Test for prawcore.Sessions module."""
from mock import patch
from prawcore.rate_limit import RateLimiter
import unittest


class RateLimiterTest(unittest.TestCase):
    def setUp(self):
        self.rate_limiter = RateLimiter()
        self.rate_limiter.next_request_timestamp = 100

    @patch('time.sleep')
    @patch('time.time')
    def test_delay(self, mock_time, mock_sleep):
        mock_time.return_value = 1
        self.rate_limiter.delay()
        self.assertTrue(mock_time.called)
        mock_sleep.assert_called_with(99)

    @patch('time.sleep')
    @patch('time.time')
    def test_delay__no_sleep_when_time_in_past(self, mock_time, mock_sleep):
        mock_time.return_value = 101
        self.rate_limiter.delay()
        self.assertTrue(mock_time.called)
        self.assertFalse(mock_sleep.called)

    @patch('time.sleep')
    def test_delay__no_sleep_when_time_is_not_set(self, mock_sleep):
        self.rate_limiter.delay()
        self.assertFalse(mock_sleep.called)

    @patch('time.sleep')
    @patch('time.time')
    def test_delay__no_sleep_when_times_match(self, mock_time, mock_sleep):
        mock_time.return_value = 100
        self.rate_limiter.delay()
        self.assertTrue(mock_time.called)
        self.assertFalse(mock_sleep.called)
