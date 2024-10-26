"""Test for prawcore.AsyncSessions module."""

import logging
from unittest.mock import Mock, patch

import pytest
from requests.exceptions import ChunkedEncodingError, ConnectionError, ReadTimeout

import prawcore
from prawcore.exceptions import RequestException

from .. import UnitTest


class AsyncInvalidAuthorizer(prawcore.AsyncAuthorizer):
    def __init__(self, requestor):
        super(AsyncInvalidAuthorizer, self).__init__(
            prawcore.AsyncTrustedAuthenticator(
                requestor,
                pytest.placeholders.client_id,
                pytest.placeholders.client_secret,
            )
        )

    def is_valid(self):
        return False


@pytest.mark.asyncio
class TestSession(UnitTest):
    @pytest.fixture
    def async_readonly_authorizer(self, async_trusted_authenticator):
        return prawcore.AsyncReadOnlyAuthorizer(async_trusted_authenticator)

    async def test_close(self, async_readonly_authorizer):
        await prawcore.AsyncSession(async_readonly_authorizer).close()

    async def test_context_manager(self, async_readonly_authorizer):
        async with prawcore.AsyncSession(async_readonly_authorizer) as session:
            assert isinstance(session, prawcore.AsyncSession)

    async def test_init__with_device_id_authorizer(self, async_untrusted_authenticator):
        authorizer = prawcore.AsyncDeviceIDAuthorizer(async_untrusted_authenticator)
        prawcore.AsyncSession(authorizer)

    async def test_init__with_implicit_authorizer(self, async_untrusted_authenticator):
        authorizer = prawcore.AsyncImplicitAuthorizer(
            async_untrusted_authenticator, None, 0, ""
        )
        prawcore.AsyncSession(authorizer)

    async def test_init__without_authenticator(self):
        with pytest.raises(prawcore.InvalidInvocation):
            prawcore.AsyncSession(None)

    @patch("requests.AsyncSession")
    @pytest.mark.parametrize(
        "exception",
        [ChunkedEncodingError(), ConnectionError(), ReadTimeout()],
        ids=["ChunkedEncodingError", "ConnectionError", "ReadTimeout"],
    )
    async def test_request__retry(self, mock_session, exception, caplog):
        caplog.set_level(logging.WARNING)
        session_instance = mock_session.return_value
        # Handle Auth
        response_dict = {"access_token": "", "expires_in": 99, "scope": ""}

        async def override():
            return Mock(headers={}, json=lambda: response_dict, status_code=200)

        session_instance.request.return_value = override()
        requestor = prawcore.AsyncRequestor("prawcore:test (by /u/bboe)")
        authenticator = prawcore.AsyncTrustedAuthenticator(
            requestor,
            pytest.placeholders.client_id,
            pytest.placeholders.client_secret,
        )
        authorizer = prawcore.AsyncReadOnlyAuthorizer(authenticator)
        await authorizer.refresh()
        session_instance.request.reset_mock()
        # Fail on subsequent request
        session_instance.request.side_effect = exception

        with pytest.raises(RequestException) as exception_info:
            await prawcore.AsyncSession(authorizer).request("GET", "/")
        assert (
            "prawcore._async",
            logging.WARNING,
            f"Retrying due to {exception.__class__.__name__}() status: GET "
            "https://oauth.reddit.com/",
        ) in caplog.record_tuples
        assert isinstance(exception_info.value, RequestException)
        assert exception is exception_info.value.original_exception
        assert session_instance.request.call_count == 3

    async def test_request__with_invalid_authorizer(self, async_requestor):
        session = prawcore.AsyncSession(AsyncInvalidAuthorizer(async_requestor))
        with pytest.raises(prawcore.InvalidInvocation):
            await session.request("get", "/")


@pytest.mark.asyncio
class TestSessionFunction(UnitTest):
    async def test_session(self, async_requestor):
        assert isinstance(
            prawcore.async_session(AsyncInvalidAuthorizer(async_requestor)),
            prawcore.AsyncSession,
        )
