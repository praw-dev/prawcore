"""Test for prawcore.requestor.Requestor class."""
import pickle

import prawcore
import unittest
from mock import patch, Mock
from prawcore import RequestException


class RequestorTest(unittest.TestCase):
    def test_initialize(self):
        requestor = prawcore.Requestor("prawcore:test (by /u/bboe)")
        self.assertEqual(
            "prawcore:test (by /u/bboe) prawcore/{}".format(
                prawcore.__version__
            ),
            requestor._http.headers["User-Agent"],
        )

    def test_initialize__failures(self):
        for agent in [None, "shorty"]:
            self.assertRaises(
                prawcore.InvalidInvocation, prawcore.Requestor, agent
            )

    @patch("requests.Session")
    def test_request__wrap_request_exceptions(self, mock_session):
        exception = Exception("prawcore wrap_request_exceptions")
        session_instance = mock_session.return_value
        session_instance.request.side_effect = exception
        requestor = prawcore.Requestor("prawcore:test (by /u/bboe)")
        with self.assertRaises(prawcore.RequestException) as context_manager:
            requestor.request("get", "http://a.b", data="bar")
        self.assertIsInstance(context_manager.exception, RequestException)
        self.assertIs(exception, context_manager.exception.original_exception)
        self.assertEqual(
            ("get", "http://a.b"), context_manager.exception.request_args
        )
        self.assertEqual(
            {"data": "bar"}, context_manager.exception.request_kwargs
        )

    def test_request__use_custom_session(self):
        override = "REQUEST OVERRIDDEN"
        custom_header = "CUSTOM SESSION HEADER"
        headers = {"session_header": custom_header}
        attrs = {"request.return_value": override, "headers": headers}
        session = Mock(**attrs)

        requestor = prawcore.Requestor(
            "prawcore:test (by /u/bboe)", session=session
        )

        self.assertEqual(
            "prawcore:test (by /u/bboe) prawcore/{}".format(
                prawcore.__version__
            ),
            requestor._http.headers["User-Agent"],
        )
        self.assertEqual(
            requestor._http.headers["session_header"], custom_header
        )

        self.assertEqual(requestor.request("https://reddit.com"), override)

    def test_pickle(self):
        requestor = prawcore.Requestor("prawcore:test (by /u/bboe)")
        for protocol in range(pickle.HIGHEST_PROTOCOL + 1):
            pickle.loads(pickle.dumps(requestor, protocol=protocol))
