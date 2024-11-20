"""Test for subclasses of prawcore._async.auth.AsyncBaseAuthenticator class."""

import pytest

import prawcore

from .. import UnitTest


class TestTrustedAuthenticator(UnitTest):
    @pytest.fixture
    def async_trusted_authenticator(self, async_trusted_authenticator):
        async_trusted_authenticator.redirect_uri = pytest.placeholders.redirect_uri
        return async_trusted_authenticator

    def test_authorize_url(self, async_trusted_authenticator):
        url = async_trusted_authenticator.authorize_url(
            "permanent", ["identity", "read"], "a_state"
        )
        assert f"client_id={pytest.placeholders.client_id}" in url
        assert "duration=permanent" in url
        assert "response_type=code" in url
        assert "scope=identity+read" in url
        assert "state=a_state" in url

    def test_authorize_url__fail_with_implicit(self, async_trusted_authenticator):
        with pytest.raises(prawcore.InvalidInvocation):
            async_trusted_authenticator.authorize_url(
                "temporary", ["identity", "read"], "a_state", implicit=True
            )

    def test_authorize_url__fail_without_redirect_uri(
        self, async_trusted_authenticator
    ):
        async_trusted_authenticator.redirect_uri = None
        with pytest.raises(prawcore.InvalidInvocation):
            async_trusted_authenticator.authorize_url(
                "permanent",
                ["identity"],
                "...",
            )


class TestUntrustedAuthenticator(UnitTest):
    @pytest.fixture
    def async_untrusted_authenticator(self, async_untrusted_authenticator):
        async_untrusted_authenticator.redirect_uri = pytest.placeholders.redirect_uri
        return async_untrusted_authenticator

    def test_authorize_url__code(self, async_untrusted_authenticator):
        url = async_untrusted_authenticator.authorize_url(
            "permanent", ["identity", "read"], "a_state"
        )
        assert f"client_id={pytest.placeholders.client_id}" in url
        assert "duration=permanent" in url
        assert "response_type=code" in url
        assert "scope=identity+read" in url
        assert "state=a_state" in url

    def test_authorize_url__fail_with_token_and_permanent(
        self, async_untrusted_authenticator
    ):
        with pytest.raises(prawcore.InvalidInvocation):
            async_untrusted_authenticator.authorize_url(
                "permanent",
                ["identity", "read"],
                "a_state",
                implicit=True,
            )

    def test_authorize_url__fail_without_redirect_uri(
        self, async_untrusted_authenticator
    ):
        async_untrusted_authenticator.redirect_uri = None
        with pytest.raises(prawcore.InvalidInvocation):
            async_untrusted_authenticator.authorize_url(
                "temporary",
                ["identity"],
                "...",
            )

    def test_authorize_url__token(self, async_untrusted_authenticator):
        url = async_untrusted_authenticator.authorize_url(
            "temporary", ["identity", "read"], "a_state", implicit=True
        )
        assert f"client_id={pytest.placeholders.client_id}" in url
        assert "duration=temporary" in url
        assert "response_type=token" in url
        assert "scope=identity+read" in url
        assert "state=a_state" in url
