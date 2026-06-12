"""Test for subclasses of prawcore.auth.BaseAuthenticator class."""

import prawcore
from tests.conftest import placeholders

from . import IntegrationTest


class TestTrustedAuthenticator(IntegrationTest):
    def test_revoke_token(self, requestor):
        authenticator = prawcore.TrustedAuthenticator(
            client_id=placeholders.client_id,
            client_secret=placeholders.client_secret,
            requestor=requestor,
        )
        authenticator.revoke_token("dummy token")

    def test_revoke_token__with_access_token_hint(self, requestor):
        authenticator = prawcore.TrustedAuthenticator(
            client_id=placeholders.client_id,
            client_secret=placeholders.client_secret,
            requestor=requestor,
        )
        authenticator.revoke_token("dummy token", token_type="access_token")

    def test_revoke_token__with_refresh_token_hint(self, requestor):
        authenticator = prawcore.TrustedAuthenticator(
            client_id=placeholders.client_id,
            client_secret=placeholders.client_secret,
            requestor=requestor,
        )
        authenticator.revoke_token("dummy token", token_type="refresh_token")


class TestUntrustedAuthenticator(IntegrationTest):
    def test_revoke_token(self, requestor):
        authenticator = prawcore.UntrustedAuthenticator(client_id=placeholders.client_id, requestor=requestor)
        authenticator.revoke_token("dummy token")
