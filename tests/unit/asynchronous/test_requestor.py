"""Test for prawcore._async.requestor.AsyncRequestor class."""

import pickle
from inspect import signature
from unittest.mock import Mock, patch

import pytest

import prawcore
from prawcore import RequestException

from .. import UnitTest


@pytest.mark.asyncio
class TestRequestor(UnitTest):
    async def test_initialize(self, async_requestor):
        assert (
            async_requestor._http.headers["User-Agent"]
            == f"prawcore:test (by /u/bboe) prawcore/{prawcore.__version__}"
        )

    async def test_initialize__failures(self):
        for agent in [None, "shorty"]:
            with pytest.raises(prawcore.InvalidInvocation):
                prawcore.AsyncRequestor(agent)

    async def test_pickle(self, async_requestor):
        for protocol in range(pickle.HIGHEST_PROTOCOL + 1):
            pickle.loads(pickle.dumps(async_requestor, protocol=protocol))

    async def test_request__session_timeout_default(self, async_requestor):
        requestor_signature = signature(async_requestor._http.request)
        assert (
            str(requestor_signature.parameters["timeout"])
            == "timeout: 'TimeoutType | None' = 120"
        )

    async def test_request__use_custom_session(self):
        async def override() -> str:
            return "ASYNC OVERRIDE"

        expected_return = await override()
        custom_header = "CUSTOM SESSION HEADER"
        headers = {"session_header": custom_header}
        attrs = {"request.return_value": override(), "headers": headers}
        session = Mock(**attrs)

        requestor = prawcore.AsyncRequestor(
            "prawcore:test (by /u/bboe)", session=session
        )

        assert (
            requestor._http.headers["User-Agent"]
            == f"prawcore:test (by /u/bboe) prawcore/{prawcore.__version__}"
        )
        assert requestor._http.headers["session_header"] == custom_header

        assert (await requestor.request("https://reddit.com")) == expected_return

    @patch("requests.AsyncSession")
    async def test_request__wrap_request_exceptions(self, mock_session):
        exception = Exception("prawcore wrap_request_exceptions")
        session_instance = mock_session.return_value
        session_instance.request.side_effect = exception
        requestor = prawcore.AsyncRequestor("prawcore:test (by /u/bboe)")
        with pytest.raises(prawcore.RequestException) as exception_info:
            await requestor.request("get", "http://a.b", data="bar")
        assert isinstance(exception_info.value, RequestException)
        assert exception is exception_info.value.original_exception
        assert exception_info.value.request_args == ("get", "http://a.b")
        assert exception_info.value.request_kwargs == {"data": "bar"}

    async def test_getattr_async_requestor(self, async_requestor):
        """This test is added to cover one line of code in the async requestor that was indirectly used by betamax"""
        adapters = getattr(async_requestor, "adapters", None)

        assert adapters is not None
