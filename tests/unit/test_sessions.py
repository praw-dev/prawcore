"""Test for prawcore.Sessions module."""
import logging

import pytest
from mock import Mock, patch
from requests.exceptions import ChunkedEncodingError, ConnectionError, ReadTimeout
from testfixtures import LogCapture

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
    def readonly_authorizer(self, refresh=True, requestor=None):
        authenticator = prawcore.TrustedAuthenticator(
            requestor or self.requestor,
            pytest.placeholders.client_id,
            pytest.placeholders.client_secret,
        )
        authorizer = prawcore.ReadOnlyAuthorizer(authenticator)
        if refresh:
            authorizer.refresh()
        return authorizer

    def test_close(self):
        prawcore.Session(self.readonly_authorizer(refresh=False)).close()

    def test_context_manager(self):
        with prawcore.Session(self.readonly_authorizer(refresh=False)) as session:
            assert isinstance(session, prawcore.Session)

    def test_init__without_authenticator(self):
        with pytest.raises(prawcore.InvalidInvocation):
            prawcore.Session(None)

    def test_init__with_device_id_authorizer(self):
        authenticator = prawcore.UntrustedAuthenticator(
            self.requestor, pytest.placeholders.client_id
        )
        authorizer = prawcore.DeviceIDAuthorizer(authenticator)
        prawcore.Session(authorizer)

    def test_init__with_implicit_authorizer(self):
        authenticator = prawcore.UntrustedAuthenticator(
            self.requestor, pytest.placeholders.client_id
        )
        authorizer = prawcore.ImplicitAuthorizer(authenticator, None, 0, "")
        prawcore.Session(authorizer)

    @patch("time.sleep", return_value=None)
    @patch("requests.Session")
    def test_request__chunked_encoding_retry(self, mock_session, _):
        session_instance = mock_session.return_value

        # Handle Auth
        response_dict = {"access_token": "", "expires_in": 99, "scope": ""}
        session_instance.request.return_value = Mock(
            headers={}, json=lambda: response_dict, status_code=200
        )
        requestor = prawcore.Requestor("prawcore:test (by /u/bboe)")
        authorizer = self.readonly_authorizer(requestor=requestor)
        session_instance.request.reset_mock()

        # Fail on subsequent request
        exception = ChunkedEncodingError()
        session_instance.request.side_effect = exception

        expected = (
            "prawcore",
            "WARNING",
            "Retrying due to ChunkedEncodingError() status: GET "
            "https://oauth.reddit.com/",
        )

        with LogCapture(level=logging.WARNING) as log_capture:
            with pytest.raises(RequestException) as exception_info:
                prawcore.Session(authorizer).request("GET", "/")
            log_capture.check(expected, expected)
        assert isinstance(exception_info.value, RequestException)
        assert exception is exception_info.value.original_exception
        assert session_instance.request.call_count == 3

    @patch("time.sleep", return_value=None)
    @patch("requests.Session")
    def test_request__connection_error_retry(self, mock_session, _):
        session_instance = mock_session.return_value

        # Handle Auth
        response_dict = {"access_token": "", "expires_in": 99, "scope": ""}
        session_instance.request.return_value = Mock(
            headers={}, json=lambda: response_dict, status_code=200
        )
        requestor = prawcore.Requestor("prawcore:test (by /u/bboe)")
        authorizer = self.readonly_authorizer(requestor=requestor)
        session_instance.request.reset_mock()

        # Fail on subsequent request
        exception = ConnectionError()
        session_instance.request.side_effect = exception

        expected = (
            "prawcore",
            "WARNING",
            "Retrying due to ConnectionError() status: GET https://oauth.reddit.com/",
        )

        with LogCapture(level=logging.WARNING) as log_capture:
            with pytest.raises(RequestException) as exception_info:
                prawcore.Session(authorizer).request("GET", "/")
            log_capture.check(expected, expected)
        assert isinstance(exception_info.value, RequestException)
        assert exception is exception_info.value.original_exception
        assert session_instance.request.call_count == 3

    @patch("time.sleep", return_value=None)
    @patch("requests.Session")
    def test_request__read_timeout_retry(self, mock_session, _):
        session_instance = mock_session.return_value

        # Handle Auth
        response_dict = {"access_token": "", "expires_in": 99, "scope": ""}
        session_instance.request.return_value = Mock(
            headers={}, json=lambda: response_dict, status_code=200
        )
        requestor = prawcore.Requestor("prawcore:test (by /u/bboe)")
        authorizer = self.readonly_authorizer(requestor=requestor)
        session_instance.request.reset_mock()

        # Fail on subsequent request
        exception = ReadTimeout()
        session_instance.request.side_effect = exception

        expected = (
            "prawcore",
            "WARNING",
            "Retrying due to ReadTimeout() status: GET https://oauth.reddit.com/",
        )

        with LogCapture(level=logging.WARNING) as log_capture:
            with pytest.raises(RequestException) as exception_info:
                prawcore.Session(authorizer).request("GET", "/")
            log_capture.check(expected, expected)
        assert isinstance(exception_info.value, RequestException)
        assert exception is exception_info.value.original_exception
        assert 3 == session_instance.request.call_count

    def test_request__with_invalid_authorizer(self):
        session = prawcore.Session(InvalidAuthorizer(self.requestor))
        with pytest.raises(prawcore.InvalidInvocation):
            session.request("get", "/")


class TestSessionFunction(UnitTest):
    def test_session(self):
        assert isinstance(
            prawcore.session(InvalidAuthorizer(self.requestor)), prawcore.Session
        )
