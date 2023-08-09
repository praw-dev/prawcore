"""Test for subclasses of prawcore.auth.BaseAuthenticator class."""
import pytest

import prawcore

from . import UnitTest


class TestTrustedAuthenticator(UnitTest):
    @pytest.fixture
    def trusted_authenticator(self, trusted_authenticator):
        trusted_authenticator.redirect_uri = pytest.placeholders.redirect_uri
        return trusted_authenticator

    def test_authorize_url(self, trusted_authenticator):
        url = trusted_authenticator.authorize_url(
            "permanent", ["identity", "read"], "a_state"
        )
        assert f"client_id={pytest.placeholders.client_id}" in url
        assert "duration=permanent" in url
        assert "response_type=code" in url
        assert "scope=identity+read" in url
        assert "state=a_state" in url

    def test_authorize_url__fail_with_implicit(self, trusted_authenticator):
        with pytest.raises(prawcore.InvalidInvocation):
            trusted_authenticator.authorize_url(
                "temporary", ["identity", "read"], "a_state", implicit=True
            )

    def test_authorize_url__fail_without_redirect_uri(self, trusted_authenticator):
        trusted_authenticator.redirect_uri = None
        with pytest.raises(prawcore.InvalidInvocation):
            trusted_authenticator.authorize_url(
                "permanent",
                ["identity"],
                "...",
            )


class TestUntrustedAuthenticator(UnitTest):
    @pytest.fixture
    def untrusted_authenticator(self, untrusted_authenticator):
        untrusted_authenticator.redirect_uri = pytest.placeholders.redirect_uri
        return untrusted_authenticator

    def test_authorize_url__code(self, untrusted_authenticator):
        url = untrusted_authenticator.authorize_url(
            "permanent", ["identity", "read"], "a_state"
        )
        assert f"client_id={pytest.placeholders.client_id}" in url
        assert "duration=permanent" in url
        assert "response_type=code" in url
        assert "scope=identity+read" in url
        assert "state=a_state" in url

    def test_authorize_url__fail_with_token_and_permanent(
        self, untrusted_authenticator
    ):
        with pytest.raises(prawcore.InvalidInvocation):
            untrusted_authenticator.authorize_url(
                "permanent",
                ["identity", "read"],
                "a_state",
                implicit=True,
            )

    def test_authorize_url__fail_without_redirect_uri(self, untrusted_authenticator):
        untrusted_authenticator.redirect_uri = None
        with pytest.raises(prawcore.InvalidInvocation):
            untrusted_authenticator.authorize_url(
                "temporary",
                ["identity"],
                "...",
            )

    def test_authorize_url__token(self, untrusted_authenticator):
        url = untrusted_authenticator.authorize_url(
            "temporary", ["identity", "read"], "a_state", implicit=True
        )
        assert f"client_id={pytest.placeholders.client_id}" in url
        assert "duration=temporary" in url
        assert "response_type=token" in url
        assert "scope=identity+read" in url
        assert "state=a_state" in url
