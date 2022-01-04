"""Test for subclasses of prawcore.auth.BaseAuthenticator class."""

import pytest

import prawcore

from . import IntegrationTest


class TestTrustedAuthenticator(IntegrationTest):
    def test_revoke_token(self):
        authenticator = prawcore.TrustedAuthenticator(
            self.requestor,
            pytest.placeholders.client_id,
            pytest.placeholders.client_secret,
        )
        with self.use_cassette("TrustedAuthenticator_revoke_token"):
            authenticator.revoke_token("dummy token")

    def test_revoke_token__with_access_token_hint(self):
        authenticator = prawcore.TrustedAuthenticator(
            self.requestor,
            pytest.placeholders.client_id,
            pytest.placeholders.client_secret,
        )
        with self.use_cassette(
            "TrustedAuthenticator_revoke_token__with_access_token_hint"
        ):
            authenticator.revoke_token("dummy token", "access_token")

    def test_revoke_token__with_refresh_token_hint(self):
        authenticator = prawcore.TrustedAuthenticator(
            self.requestor,
            pytest.placeholders.client_id,
            pytest.placeholders.client_secret,
        )
        with self.use_cassette(
            "TrustedAuthenticator_revoke_token__with_refresh_token_hint"
        ):
            authenticator.revoke_token("dummy token", "refresh_token")


class TestUntrustedAuthenticator(IntegrationTest):
    def test_revoke_token(self):
        authenticator = prawcore.UntrustedAuthenticator(
            self.requestor, pytest.placeholders.client_id
        )
        with self.use_cassette("UntrustedAuthenticator_revoke_token"):
            authenticator.revoke_token("dummy token")
