"""Test for prawcore.auth.Authorizer classes."""

import pytest

import prawcore

from . import IntegrationTest


class TestAuthorizer(IntegrationTest):
    def test_authorize__with_invalid_code(self, trusted_authenticator):
        trusted_authenticator.redirect_uri = pytest.placeholders.redirect_uri
        authorizer = prawcore.Authorizer(trusted_authenticator)
        with pytest.raises(prawcore.OAuthException):
            authorizer.authorize("invalid code")
        assert not authorizer.is_valid()

    def test_authorize__with_permanent_grant(self, trusted_authenticator):
        trusted_authenticator.redirect_uri = pytest.placeholders.redirect_uri
        authorizer = prawcore.Authorizer(trusted_authenticator)
        authorizer.authorize(pytest.placeholders.permanent_grant_code)

        assert authorizer.access_token is not None
        assert authorizer.refresh_token is not None
        assert isinstance(authorizer.scopes, set)
        assert len(authorizer.scopes) > 0
        assert authorizer.is_valid()

    def test_authorize__with_temporary_grant(self, trusted_authenticator):
        trusted_authenticator.redirect_uri = pytest.placeholders.redirect_uri
        authorizer = prawcore.Authorizer(trusted_authenticator)
        authorizer.authorize(pytest.placeholders.temporary_grant_code)

        assert authorizer.access_token is not None
        assert authorizer.refresh_token is None
        assert isinstance(authorizer.scopes, set)
        assert len(authorizer.scopes) > 0
        assert authorizer.is_valid()

    def test_refresh(self, trusted_authenticator):
        authorizer = prawcore.Authorizer(trusted_authenticator, refresh_token=pytest.placeholders.refresh_token)
        authorizer.refresh()

        assert authorizer.access_token is not None
        assert isinstance(authorizer.scopes, set)
        assert len(authorizer.scopes) > 0
        assert authorizer.is_valid()

    @pytest.mark.cassette_name("TestAuthorizer.test_refresh")
    def test_refresh__post_refresh_callback(self, trusted_authenticator):
        def callback(authorizer):
            assert authorizer.refresh_token != pytest.placeholders.refresh_token
            authorizer.refresh_token = "manually_updated"

        authorizer = prawcore.Authorizer(
            trusted_authenticator,
            post_refresh_callback=callback,
            refresh_token=pytest.placeholders.refresh_token,
        )
        authorizer.refresh()

        assert authorizer.access_token is not None
        assert authorizer.refresh_token == "manually_updated"
        assert isinstance(authorizer.scopes, set)
        assert len(authorizer.scopes) > 0
        assert authorizer.is_valid()

    @pytest.mark.cassette_name("TestAuthorizer.test_refresh")
    def test_refresh__pre_refresh_callback(self, trusted_authenticator):
        def callback(authorizer):
            assert authorizer.refresh_token is None
            authorizer.refresh_token = pytest.placeholders.refresh_token

        authorizer = prawcore.Authorizer(trusted_authenticator, pre_refresh_callback=callback)
        authorizer.refresh()

        assert authorizer.access_token is not None
        assert isinstance(authorizer.scopes, set)
        assert len(authorizer.scopes) > 0
        assert authorizer.is_valid()

    def test_refresh__with_invalid_token(self, trusted_authenticator):
        authorizer = prawcore.Authorizer(trusted_authenticator, refresh_token="INVALID_TOKEN")
        with pytest.raises(prawcore.ResponseException):
            authorizer.refresh()
        assert not authorizer.is_valid()

    def test_revoke__access_token_with_refresh_set(self, trusted_authenticator):
        authorizer = prawcore.Authorizer(trusted_authenticator, refresh_token=pytest.placeholders.refresh_token)
        authorizer.refresh()
        authorizer.revoke(only_access=True)

        assert authorizer.access_token is None
        assert authorizer.refresh_token is not None
        assert authorizer.scopes is None
        assert not authorizer.is_valid()

        authorizer.refresh()

        assert authorizer.is_valid()

    def test_revoke__access_token_without_refresh_set(self, trusted_authenticator):
        trusted_authenticator.redirect_uri = pytest.placeholders.redirect_uri
        authorizer = prawcore.Authorizer(trusted_authenticator)
        authorizer.authorize(pytest.placeholders.temporary_grant_code)
        authorizer.revoke()

        assert authorizer.access_token is None
        assert authorizer.refresh_token is None
        assert authorizer.scopes is None
        assert not authorizer.is_valid()

    def test_revoke__refresh_token_with_access_set(self, trusted_authenticator):
        authorizer = prawcore.Authorizer(trusted_authenticator, refresh_token=pytest.placeholders.refresh_token)
        authorizer.refresh()
        authorizer.revoke()

        assert authorizer.access_token is None
        assert authorizer.refresh_token is None
        assert authorizer.scopes is None
        assert not authorizer.is_valid()

    def test_revoke__refresh_token_without_access_set(self, trusted_authenticator):
        authorizer = prawcore.Authorizer(trusted_authenticator, refresh_token=pytest.placeholders.refresh_token)
        authorizer.revoke()

        assert authorizer.access_token is None
        assert authorizer.refresh_token is None
        assert authorizer.scopes is None
        assert not authorizer.is_valid()


class TestDeviceIDAuthorizer(IntegrationTest):
    def test_refresh(self, untrusted_authenticator):
        authorizer = prawcore.DeviceIDAuthorizer(untrusted_authenticator)
        authorizer.refresh()

        assert authorizer.access_token is not None
        assert authorizer.scopes == {"*"}
        assert authorizer.is_valid()

    def test_refresh__with_scopes_and_trusted_authenticator(self, requestor):
        scope_list = {"adsedit", "adsread", "creddits", "history"}
        authorizer = prawcore.DeviceIDAuthorizer(
            prawcore.TrustedAuthenticator(
                requestor,
                pytest.placeholders.client_id,
                pytest.placeholders.client_secret,
            ),
            scopes=scope_list,
        )
        authorizer.refresh()

        assert authorizer.access_token is not None
        assert authorizer.scopes == scope_list
        assert authorizer.is_valid()

    def test_refresh__with_short_device_id(self, untrusted_authenticator):
        authorizer = prawcore.DeviceIDAuthorizer(untrusted_authenticator, "a" * 19)
        with pytest.raises(prawcore.OAuthException):
            authorizer.refresh()


class TestReadOnlyAuthorizer(IntegrationTest):
    def test_refresh(self, trusted_authenticator):
        authorizer = prawcore.ReadOnlyAuthorizer(trusted_authenticator)
        assert authorizer.access_token is None
        assert authorizer.scopes is None
        assert not authorizer.is_valid()
        authorizer.refresh()

        assert authorizer.access_token is not None
        assert authorizer.scopes == {"*"}
        assert authorizer.is_valid()

    def test_refresh__with_scopes(self, trusted_authenticator):
        scope_list = {"adsedit", "adsread", "creddits", "history"}
        authorizer = prawcore.ReadOnlyAuthorizer(trusted_authenticator, scopes=scope_list)
        assert authorizer.access_token is None
        assert authorizer.scopes is None
        assert not authorizer.is_valid()
        authorizer.refresh()

        assert authorizer.access_token is not None
        assert authorizer.scopes == scope_list
        assert authorizer.is_valid()


class TestScriptAuthorizer(IntegrationTest):
    def test_refresh(self, trusted_authenticator):
        authorizer = prawcore.ScriptAuthorizer(
            trusted_authenticator,
            pytest.placeholders.username,
            pytest.placeholders.password,
        )
        assert authorizer.access_token is None
        assert authorizer.scopes is None
        assert not authorizer.is_valid()
        authorizer.refresh()

        assert authorizer.access_token is not None
        assert authorizer.scopes == {"*"}
        assert authorizer.is_valid()

    def test_refresh__with_invalid_otp(self, trusted_authenticator):
        authorizer = prawcore.ScriptAuthorizer(
            trusted_authenticator,
            pytest.placeholders.username,
            pytest.placeholders.password,
            lambda: "fake",
        )
        with pytest.raises(prawcore.OAuthException):
            authorizer.refresh()
        assert not authorizer.is_valid()

    def test_refresh__with_invalid_username_or_password(self, trusted_authenticator):
        authorizer = prawcore.ScriptAuthorizer(trusted_authenticator, pytest.placeholders.username, "invalidpassword")
        with pytest.raises(prawcore.OAuthException):
            authorizer.refresh()
        assert not authorizer.is_valid()

    def test_refresh__with_scopes(self, trusted_authenticator):
        scope_list = {"adsedit", "adsread", "creddits", "history"}
        authorizer = prawcore.ScriptAuthorizer(
            trusted_authenticator,
            pytest.placeholders.username,
            pytest.placeholders.password,
            scopes=scope_list,
        )
        authorizer.refresh()

        assert authorizer.access_token is not None
        assert authorizer.scopes == scope_list
        assert authorizer.is_valid()

    def test_refresh__with_valid_otp(self, trusted_authenticator):
        authorizer = prawcore.ScriptAuthorizer(
            trusted_authenticator,
            pytest.placeholders.username,
            pytest.placeholders.password,
            lambda: "000000",
        )
        assert authorizer.access_token is None
        assert authorizer.scopes is None
        assert not authorizer.is_valid()
        authorizer.refresh()

        assert authorizer.access_token is not None
        assert authorizer.scopes == {"*"}
        assert authorizer.is_valid()
