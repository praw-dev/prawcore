"""Test for prawcore._async.auth.AsyncAuthorizer classes."""

import pytest

import prawcore

from .. import UnitTest


class AsyncInvalidAuthenticator(prawcore._async.auth.AsyncBaseAuthenticator):
    def _auth(self):
        pass


@pytest.mark.asyncio
class TestAuthorizer(UnitTest):
    async def test_authorize__fail_without_redirect_uri(
        self, async_trusted_authenticator
    ):
        authorizer = prawcore.AsyncAuthorizer(async_trusted_authenticator)
        with pytest.raises(prawcore.InvalidInvocation):
            await authorizer.authorize("dummy code")
        assert not authorizer.is_valid()

    async def test_initialize(self, async_trusted_authenticator):
        authorizer = prawcore.AsyncAuthorizer(async_trusted_authenticator)
        assert authorizer.access_token is None
        assert authorizer.scopes is None
        assert authorizer.refresh_token is None
        assert not authorizer.is_valid()

    async def test_initialize__with_refresh_token(self, async_trusted_authenticator):
        authorizer = prawcore.AsyncAuthorizer(
            async_trusted_authenticator, refresh_token=pytest.placeholders.refresh_token
        )
        assert authorizer.access_token is None
        assert authorizer.scopes is None
        assert pytest.placeholders.refresh_token == authorizer.refresh_token
        assert not authorizer.is_valid()

    async def test_initialize__with_untrusted_authenticator(self):
        authenticator = prawcore.AsyncUntrustedAuthenticator(None, None)
        authorizer = prawcore.AsyncAuthorizer(authenticator)
        assert authorizer.access_token is None
        assert authorizer.scopes is None
        assert authorizer.refresh_token is None
        assert not authorizer.is_valid()

    async def test_refresh__without_refresh_token(self, async_trusted_authenticator):
        authorizer = prawcore.AsyncAuthorizer(async_trusted_authenticator)
        with pytest.raises(prawcore.InvalidInvocation):
            await authorizer.refresh()
        assert not authorizer.is_valid()

    async def test_revoke__without_access_token(self, async_trusted_authenticator):
        authorizer = prawcore.AsyncAuthorizer(
            async_trusted_authenticator, refresh_token=pytest.placeholders.refresh_token
        )
        with pytest.raises(prawcore.InvalidInvocation):
            await authorizer.revoke(only_access=True)

    async def test_revoke__without_any_token(self, async_trusted_authenticator):
        authorizer = prawcore.AsyncAuthorizer(async_trusted_authenticator)
        with pytest.raises(prawcore.InvalidInvocation):
            await authorizer.revoke()


@pytest.mark.asyncio
class TestDeviceIDAuthorizer(UnitTest):
    async def test_initialize(self, async_untrusted_authenticator):
        authorizer = prawcore.AsyncDeviceIDAuthorizer(async_untrusted_authenticator)
        assert authorizer.access_token is None
        assert authorizer.scopes is None
        assert not authorizer.is_valid()

    async def test_initialize__with_invalid_authenticator(self):
        authenticator = prawcore.AsyncAuthorizer(
            AsyncInvalidAuthenticator(None, None, None)
        )
        with pytest.raises(prawcore.InvalidInvocation):
            prawcore.AsyncDeviceIDAuthorizer(authenticator)


@pytest.mark.asyncio
class TestImplicitAuthorizer(UnitTest):
    async def test_initialize(self, async_untrusted_authenticator):
        authorizer = prawcore.AsyncImplicitAuthorizer(
            async_untrusted_authenticator, "fake token", 1, "modposts read"
        )
        assert authorizer.access_token == "fake token"
        assert authorizer.scopes == {"modposts", "read"}
        assert authorizer.is_valid()

    async def test_initialize__with_trusted_authenticator(
        self, async_trusted_authenticator
    ):
        with pytest.raises(prawcore.InvalidInvocation):
            prawcore.AsyncImplicitAuthorizer(
                async_trusted_authenticator, None, None, None
            )


@pytest.mark.asyncio
class TestReadOnlyAuthorizer(UnitTest):
    async def test_initialize__with_untrusted_authenticator(
        self, async_untrusted_authenticator
    ):
        with pytest.raises(prawcore.InvalidInvocation):
            prawcore.AsyncReadOnlyAuthorizer(async_untrusted_authenticator)


@pytest.mark.asyncio
class TestScriptAuthorizer(UnitTest):
    async def test_initialize__with_untrusted_authenticator(
        self, async_untrusted_authenticator
    ):
        with pytest.raises(prawcore.InvalidInvocation):
            prawcore.AsyncScriptAuthorizer(async_untrusted_authenticator, None, None)
