"""Test for prawcore.auth.Authorizer classes."""

import pytest

import prawcore

from . import AsyncIntegrationTest


class TestAuthorizer(AsyncIntegrationTest):
    async def test_authorize__with_invalid_code(self, async_trusted_authenticator):
        async_trusted_authenticator.redirect_uri = pytest.placeholders.redirect_uri
        authorizer = prawcore.AsyncAuthorizer(async_trusted_authenticator)
        with pytest.raises(prawcore.OAuthException):
            await authorizer.authorize("invalid code")
        assert not authorizer.is_valid()

    async def test_authorize__with_permanent_grant(self, async_trusted_authenticator):
        async_trusted_authenticator.redirect_uri = pytest.placeholders.redirect_uri
        authorizer = prawcore.AsyncAuthorizer(async_trusted_authenticator)
        await authorizer.authorize(pytest.placeholders.permanent_grant_code)

        assert authorizer.access_token is not None
        assert authorizer.refresh_token is not None
        assert isinstance(authorizer.scopes, set)
        assert len(authorizer.scopes) > 0
        assert authorizer.is_valid()

    async def test_authorize__with_temporary_grant(self, async_trusted_authenticator):
        async_trusted_authenticator.redirect_uri = pytest.placeholders.redirect_uri
        authorizer = prawcore.AsyncAuthorizer(async_trusted_authenticator)
        await authorizer.authorize(pytest.placeholders.temporary_grant_code)

        assert authorizer.access_token is not None
        assert authorizer.refresh_token is None
        assert isinstance(authorizer.scopes, set)
        assert len(authorizer.scopes) > 0
        assert authorizer.is_valid()

    async def test_refresh(self, async_trusted_authenticator):
        authorizer = prawcore.AsyncAuthorizer(
            async_trusted_authenticator, refresh_token=pytest.placeholders.refresh_token
        )
        await authorizer.refresh()

        assert authorizer.access_token is not None
        assert isinstance(authorizer.scopes, set)
        assert len(authorizer.scopes) > 0
        assert authorizer.is_valid()

    @pytest.mark.cassette_name("TestAuthorizer.test_refresh")
    async def test_refresh__post_refresh_callback(self, async_trusted_authenticator):
        async def callback(authorizer):
            assert authorizer.refresh_token != pytest.placeholders.refresh_token
            authorizer.refresh_token = "manually_updated"

        authorizer = prawcore.AsyncAuthorizer(
            async_trusted_authenticator,
            post_refresh_callback=callback,
            refresh_token=pytest.placeholders.refresh_token,
        )
        await authorizer.refresh()

        assert authorizer.access_token is not None
        assert authorizer.refresh_token == "manually_updated"
        assert isinstance(authorizer.scopes, set)
        assert len(authorizer.scopes) > 0
        assert authorizer.is_valid()

    @pytest.mark.cassette_name("TestAuthorizer.test_refresh")
    async def test_refresh__pre_refresh_callback(self, async_trusted_authenticator):
        async def callback(authorizer):
            assert authorizer.refresh_token is None
            authorizer.refresh_token = pytest.placeholders.refresh_token

        authorizer = prawcore.AsyncAuthorizer(
            async_trusted_authenticator, pre_refresh_callback=callback
        )
        await authorizer.refresh()

        assert authorizer.access_token is not None
        assert isinstance(authorizer.scopes, set)
        assert len(authorizer.scopes) > 0
        assert authorizer.is_valid()

    async def test_refresh__with_invalid_token(self, async_trusted_authenticator):
        authorizer = prawcore.AsyncAuthorizer(
            async_trusted_authenticator, refresh_token="INVALID_TOKEN"
        )
        with pytest.raises(prawcore.ResponseException):
            await authorizer.refresh()
        assert not authorizer.is_valid()

    async def test_revoke__access_token_with_refresh_set(self, async_trusted_authenticator):
        authorizer = prawcore.AsyncAuthorizer(
            async_trusted_authenticator, refresh_token=pytest.placeholders.refresh_token
        )
        await authorizer.refresh()
        await authorizer.revoke(only_access=True)

        assert authorizer.access_token is None
        assert authorizer.refresh_token is not None
        assert authorizer.scopes is None
        assert not authorizer.is_valid()

        await authorizer.refresh()

        assert authorizer.is_valid()

    async def test_revoke__access_token_without_refresh_set(self, async_trusted_authenticator):
        async_trusted_authenticator.redirect_uri = pytest.placeholders.redirect_uri
        authorizer = prawcore.AsyncAuthorizer(async_trusted_authenticator)
        await authorizer.authorize(pytest.placeholders.temporary_grant_code)
        await authorizer.revoke()

        assert authorizer.access_token is None
        assert authorizer.refresh_token is None
        assert authorizer.scopes is None
        assert not authorizer.is_valid()

    async def test_revoke__refresh_token_with_access_set(self, async_trusted_authenticator):
        authorizer = prawcore.AsyncAuthorizer(
            async_trusted_authenticator, refresh_token=pytest.placeholders.refresh_token
        )
        await authorizer.refresh()
        await authorizer.revoke()

        assert authorizer.access_token is None
        assert authorizer.refresh_token is None
        assert authorizer.scopes is None
        assert not authorizer.is_valid()

    async def test_revoke__refresh_token_without_access_set(self, async_trusted_authenticator):
        authorizer = prawcore.AsyncAuthorizer(
            async_trusted_authenticator, refresh_token=pytest.placeholders.refresh_token
        )
        await authorizer.revoke()

        assert authorizer.access_token is None
        assert authorizer.refresh_token is None
        assert authorizer.scopes is None
        assert not authorizer.is_valid()


class TestDeviceIDAuthorizer(AsyncIntegrationTest):
    async def test_refresh(self, async_untrusted_authenticator):
        authorizer = prawcore.AsyncDeviceIDAuthorizer(async_untrusted_authenticator)
        await authorizer.refresh()

        assert authorizer.access_token is not None
        assert authorizer.scopes == {"*"}
        assert authorizer.is_valid()

    async def test_refresh__with_scopes_and_trusted_authenticator(
        self, async_requestor, async_untrusted_authenticator
    ):
        scope_list = {"adsedit", "adsread", "creddits", "history"}
        authorizer = prawcore.AsyncDeviceIDAuthorizer(
            prawcore.AsyncTrustedAuthenticator(
                async_requestor,
                pytest.placeholders.client_id,
                pytest.placeholders.client_secret,
            ),
            scopes=scope_list,
        )
        await authorizer.refresh()

        assert authorizer.access_token is not None
        assert authorizer.scopes == scope_list
        assert authorizer.is_valid()

    async def test_refresh__with_short_device_id(self, async_untrusted_authenticator):
        authorizer = prawcore.AsyncDeviceIDAuthorizer(async_untrusted_authenticator, "a" * 19)
        with pytest.raises(prawcore.OAuthException):
            await authorizer.refresh()


class TestReadOnlyAuthorizer(AsyncIntegrationTest):
    async def test_refresh(self, async_trusted_authenticator):
        authorizer = prawcore.AsyncReadOnlyAuthorizer(async_trusted_authenticator)
        assert authorizer.access_token is None
        assert authorizer.scopes is None
        assert not authorizer.is_valid()
        await authorizer.refresh()

        assert authorizer.access_token is not None
        assert authorizer.scopes == {"*"}
        assert authorizer.is_valid()

    async def test_refresh__with_scopes(self, async_trusted_authenticator):
        scope_list = {"adsedit", "adsread", "creddits", "history"}
        authorizer = prawcore.AsyncReadOnlyAuthorizer(
            async_trusted_authenticator, scopes=scope_list
        )
        assert authorizer.access_token is None
        assert authorizer.scopes is None
        assert not authorizer.is_valid()
        await authorizer.refresh()

        assert authorizer.access_token is not None
        assert authorizer.scopes == scope_list
        assert authorizer.is_valid()


class TestScriptAuthorizer(AsyncIntegrationTest):
    async def test_refresh(self, async_trusted_authenticator):
        authorizer = prawcore.AsyncScriptAuthorizer(
            async_trusted_authenticator,
            pytest.placeholders.username,
            pytest.placeholders.password,
        )
        assert authorizer.access_token is None
        assert authorizer.scopes is None
        assert not authorizer.is_valid()
        await authorizer.refresh()

        assert authorizer.access_token is not None
        assert authorizer.scopes == {"*"}
        assert authorizer.is_valid()

    async def test_refresh__with_invalid_otp(self, async_trusted_authenticator):
        authorizer = prawcore.AsyncScriptAuthorizer(
            async_trusted_authenticator,
            pytest.placeholders.username,
            pytest.placeholders.password,
            lambda: "fake",
        )
        with pytest.raises(prawcore.OAuthException):
            await authorizer.refresh()
        assert not authorizer.is_valid()

    async def test_refresh__with_invalid_username_or_password(self, async_trusted_authenticator):
        authorizer = prawcore.AsyncScriptAuthorizer(
            async_trusted_authenticator, pytest.placeholders.username, "invalidpassword"
        )
        with pytest.raises(prawcore.OAuthException):
            await authorizer.refresh()
        assert not authorizer.is_valid()

    async def test_refresh__with_scopes(self, async_trusted_authenticator):
        scope_list = {"adsedit", "adsread", "creddits", "history"}
        authorizer = prawcore.AsyncScriptAuthorizer(
            async_trusted_authenticator,
            pytest.placeholders.username,
            pytest.placeholders.password,
            scopes=scope_list,
        )
        await authorizer.refresh()

        assert authorizer.access_token is not None
        assert authorizer.scopes == scope_list
        assert authorizer.is_valid()

    async def test_refresh__with_valid_otp(self, async_trusted_authenticator):
        authorizer = prawcore.AsyncScriptAuthorizer(
            async_trusted_authenticator,
            pytest.placeholders.username,
            pytest.placeholders.password,
            lambda: "000000",
        )
        assert authorizer.access_token is None
        assert authorizer.scopes is None
        assert not authorizer.is_valid()
        await authorizer.refresh()

        assert authorizer.access_token is not None
        assert authorizer.scopes == {"*"}
        assert authorizer.is_valid()
