"""Test for subclasses of prawcore.auth.BaseAuthenticator class."""

import pytest

import prawcore

from . import AsyncIntegrationTest


class TestTrustedAuthenticator(AsyncIntegrationTest):
    async def test_revoke_token(self, async_requestor):
        authenticator = prawcore.AsyncTrustedAuthenticator(
            async_requestor,
            pytest.placeholders.client_id,
            pytest.placeholders.client_secret,
        )
        await authenticator.revoke_token("dummy token")

    async def test_revoke_token__with_access_token_hint(self, async_requestor):
        authenticator = prawcore.AsyncTrustedAuthenticator(
            async_requestor,
            pytest.placeholders.client_id,
            pytest.placeholders.client_secret,
        )
        await authenticator.revoke_token("dummy token", "access_token")

    async def test_revoke_token__with_refresh_token_hint(self, async_requestor):
        authenticator = prawcore.AsyncTrustedAuthenticator(
            async_requestor,
            pytest.placeholders.client_id,
            pytest.placeholders.client_secret,
        )
        await authenticator.revoke_token("dummy token", "refresh_token")


class TestUntrustedAuthenticator(AsyncIntegrationTest):
    async def test_revoke_token(self, async_requestor):
        authenticator = prawcore.AsyncUntrustedAuthenticator(
            async_requestor, pytest.placeholders.client_id
        )
        await authenticator.revoke_token("dummy token")
