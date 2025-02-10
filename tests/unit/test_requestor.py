"""Test for prawcore.self.requestor.Requestor class."""

import pickle
from inspect import signature
from unittest.mock import Mock, patch

import pytest

import prawcore
from prawcore import RequestException

from . import UnitTest


class TestRequestor(UnitTest):
    def test_initialize(self, requestor):
        assert requestor._http.headers["User-Agent"] == f"prawcore:test (by /u/bboe) prawcore/{prawcore.__version__}"

    def test_initialize__failures(self):
        for agent in [None, "shorty"]:
            with pytest.raises(prawcore.InvalidInvocation):
                prawcore.Requestor(agent)

    def test_pickle(self, requestor):
        for protocol in range(pickle.HIGHEST_PROTOCOL + 1):
            pickle.loads(pickle.dumps(requestor, protocol=protocol))

    def test_request__session_timeout_default(self, requestor):
        requestor_signature = signature(requestor._http.request)
        assert str(requestor_signature.parameters["timeout"]) == "timeout=None"

    def test_request__use_custom_session(self):
        override = "REQUEST OVERRIDDEN"
        custom_header = "CUSTOM SESSION HEADER"
        headers = {"session_header": custom_header}
        attrs = {"request.return_value": override, "headers": headers}
        session = Mock(**attrs)

        requestor = prawcore.Requestor("prawcore:test (by /u/bboe)", session=session)

        assert requestor._http.headers["User-Agent"] == f"prawcore:test (by /u/bboe) prawcore/{prawcore.__version__}"
        assert requestor._http.headers["session_header"] == custom_header

        assert requestor.request("https://reddit.com") == override

    @patch("requests.Session")
    def test_request__wrap_request_exceptions(self, mock_session):
        exception = Exception("prawcore wrap_request_exceptions")
        session_instance = mock_session.return_value
        session_instance.request.side_effect = exception
        requestor = prawcore.Requestor("prawcore:test (by /u/bboe)")
        with pytest.raises(prawcore.RequestException) as exception_info:
            requestor.request("get", "http://a.b", data="bar")
        assert isinstance(exception_info.value, RequestException)
        assert exception is exception_info.value.original_exception
        assert exception_info.value.request_args == ("get", "http://a.b")
        assert exception_info.value.request_kwargs == {"data": "bar"}
