"""Test for prawcore.Sessions module."""

import logging
from unittest.mock import Mock, patch

import pytest
from requests.exceptions import ChunkedEncodingError, ConnectionError, ReadTimeout

import prawcore
from prawcore.exceptions import RequestException

from . import UnitTest


class InvalidAuthorizer(prawcore.Authorizer):
    def __init__(self, requestor):
        super(InvalidAuthorizer, self).__init__(
            prawcore.TrustedAuthenticator(
                requestor,
                pytest.placeholders.client_id,
                pytest.placeholders.client_secret,
            )
        )

    def is_valid(self):
        return False


class TestSession(UnitTest):
    @pytest.fixture
    def readonly_authorizer(self, trusted_authenticator):
        return prawcore.ReadOnlyAuthorizer(trusted_authenticator)

    def test_close(self, readonly_authorizer):
        prawcore.Session(readonly_authorizer).close()

    def test_context_manager(self, readonly_authorizer):
        with prawcore.Session(readonly_authorizer) as session:
            assert isinstance(session, prawcore.Session)

    def test_init__with_device_id_authorizer(self, untrusted_authenticator):
        authorizer = prawcore.DeviceIDAuthorizer(untrusted_authenticator)
        prawcore.Session(authorizer)

    def test_init__with_implicit_authorizer(self, untrusted_authenticator):
        authorizer = prawcore.ImplicitAuthorizer(untrusted_authenticator, None, 0, "")
        prawcore.Session(authorizer)

    def test_init__without_authenticator(self):
        with pytest.raises(prawcore.InvalidInvocation):
            prawcore.Session(None)

    @patch("requests.Session")
    @pytest.mark.parametrize(
        "exception",
        [ChunkedEncodingError(), ConnectionError(), ReadTimeout()],
        ids=["ChunkedEncodingError", "ConnectionError", "ReadTimeout"],
    )
    def test_request__retry(self, mock_session, exception, caplog):
        caplog.set_level(logging.WARNING)
        session_instance = mock_session.return_value
        # Handle Auth
        response_dict = {"access_token": "", "expires_in": 99, "scope": ""}
        session_instance.request.return_value = Mock(
            headers={}, json=lambda: response_dict, status_code=200
        )
        requestor = prawcore.Requestor("prawcore:test (by /u/bboe)")
        authenticator = prawcore.TrustedAuthenticator(
            requestor,
            pytest.placeholders.client_id,
            pytest.placeholders.client_secret,
        )
        authorizer = prawcore.ReadOnlyAuthorizer(authenticator)
        authorizer.refresh()
        session_instance.request.reset_mock()
        # Fail on subsequent request
        session_instance.request.side_effect = exception

        with pytest.raises(RequestException) as exception_info:
            prawcore.Session(authorizer).request("GET", "/")
        assert (
            "prawcore",
            logging.WARNING,
            f"Retrying due to {exception.__class__.__name__}() status: GET "
            "https://oauth.reddit.com/",
        ) in caplog.record_tuples
        assert isinstance(exception_info.value, RequestException)
        assert exception is exception_info.value.original_exception
        assert session_instance.request.call_count == 3

    def test_request__with_invalid_authorizer(self, requestor):
        session = prawcore.Session(InvalidAuthorizer(requestor))
        with pytest.raises(prawcore.InvalidInvocation):
            session.request("get", "/")


class TestSessionFunction(UnitTest):
    def test_session(self, requestor):
        assert isinstance(
            prawcore.session(InvalidAuthorizer(requestor)), prawcore.Session
        )
