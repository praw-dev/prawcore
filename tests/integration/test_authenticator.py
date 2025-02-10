"""Test for subclasses of prawcore.auth.BaseAuthenticator class."""

import pytest

import prawcore

from . import IntegrationTest


class TestTrustedAuthenticator(IntegrationTest):
    def test_revoke_token(self, requestor):
        authenticator = prawcore.TrustedAuthenticator(
            requestor,
            pytest.placeholders.client_id,
            pytest.placeholders.client_secret,
        )
        authenticator.revoke_token("dummy token")

    def test_revoke_token__with_access_token_hint(self, requestor):
        authenticator = prawcore.TrustedAuthenticator(
            requestor,
            pytest.placeholders.client_id,
            pytest.placeholders.client_secret,
        )
        authenticator.revoke_token("dummy token", "access_token")

    def test_revoke_token__with_refresh_token_hint(self, requestor):
        authenticator = prawcore.TrustedAuthenticator(
            requestor,
            pytest.placeholders.client_id,
            pytest.placeholders.client_secret,
        )
        authenticator.revoke_token("dummy token", "refresh_token")


class TestUntrustedAuthenticator(IntegrationTest):
    def test_revoke_token(self, requestor):
        authenticator = prawcore.UntrustedAuthenticator(requestor, pytest.placeholders.client_id)
        authenticator.revoke_token("dummy token")
