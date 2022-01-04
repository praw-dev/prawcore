"""Test for prawcore.auth.Authorizer classes."""
import pytest

import prawcore

from ..conftest import two_factor_callback  # noqa F401
from . import IntegrationTest


class AuthorizerBase(IntegrationTest):
    def setup(self):
        super().setup()
        self.authentication = prawcore.TrustedAuthenticator(
            self.requestor,
            pytest.placeholders.client_id,
            pytest.placeholders.client_secret,
        )


class TestAuthorizer(AuthorizerBase):
    def test_authorize__with_permanent_grant(self):
        self.authentication.redirect_uri = pytest.placeholders.redirect_uri
        authorizer = prawcore.Authorizer(self.authentication)
        with self.use_cassette():
            authorizer.authorize(pytest.placeholders.permanent_grant_code)

        assert authorizer.access_token is not None
        assert authorizer.refresh_token is not None
        assert isinstance(authorizer.scopes, set)
        assert len(authorizer.scopes) > 0
        assert authorizer.is_valid()

    def test_authorize__with_temporary_grant(self):
        self.authentication.redirect_uri = pytest.placeholders.redirect_uri
        authorizer = prawcore.Authorizer(self.authentication)
        with self.use_cassette():
            authorizer.authorize(pytest.placeholders.temporary_grant_code)

        assert authorizer.access_token is not None
        assert authorizer.refresh_token is None
        assert isinstance(authorizer.scopes, set)
        assert len(authorizer.scopes) > 0
        assert authorizer.is_valid()

    def test_authorize__with_invalid_code(self):
        self.authentication.redirect_uri = pytest.placeholders.redirect_uri
        authorizer = prawcore.Authorizer(self.authentication)
        with self.use_cassette():
            with pytest.raises(prawcore.OAuthException):
                authorizer.authorize("invalid code")
        assert not authorizer.is_valid()

    def test_refresh(self):
        authorizer = prawcore.Authorizer(
            self.authentication, refresh_token=pytest.placeholders.refresh_token
        )
        with self.use_cassette():
            authorizer.refresh()

        assert authorizer.access_token is not None
        assert isinstance(authorizer.scopes, set)
        assert len(authorizer.scopes) > 0
        assert authorizer.is_valid()

    def test_refresh__post_refresh_callback(self):
        def callback(authorizer):
            assert authorizer.refresh_token != pytest.placeholders.refresh_token
            authorizer.refresh_token = "manually_updated"

        authorizer = prawcore.Authorizer(
            self.authentication,
            post_refresh_callback=callback,
            refresh_token=pytest.placeholders.refresh_token,
        )
        with self.use_cassette("TestAuthorizer.test_refresh"):
            authorizer.refresh()

        assert authorizer.access_token is not None
        assert authorizer.refresh_token == "manually_updated"
        assert isinstance(authorizer.scopes, set)
        assert len(authorizer.scopes) > 0
        assert authorizer.is_valid()

    def test_refresh__pre_refresh_callback(self):
        def callback(authorizer):
            assert authorizer.refresh_token is None
            authorizer.refresh_token = pytest.placeholders.refresh_token

        authorizer = prawcore.Authorizer(
            self.authentication, pre_refresh_callback=callback
        )
        with self.use_cassette("TestAuthorizer.test_refresh"):
            authorizer.refresh()

        assert authorizer.access_token is not None
        assert isinstance(authorizer.scopes, set)
        assert len(authorizer.scopes) > 0
        assert authorizer.is_valid()

    def test_refresh__with_invalid_token(self):
        authorizer = prawcore.Authorizer(
            self.authentication, refresh_token="INVALID_TOKEN"
        )
        with self.use_cassette():
            with pytest.raises(prawcore.ResponseException):
                authorizer.refresh()
            assert not authorizer.is_valid()

    def test_revoke__access_token_with_refresh_set(self):
        authorizer = prawcore.Authorizer(
            self.authentication, refresh_token=pytest.placeholders.refresh_token
        )
        with self.use_cassette():
            authorizer.refresh()
            authorizer.revoke(only_access=True)

            assert authorizer.access_token is None
            assert authorizer.refresh_token is not None
            assert authorizer.scopes is None
            assert not authorizer.is_valid()

            authorizer.refresh()

        assert authorizer.is_valid()

    def test_revoke__access_token_without_refresh_set(self):
        self.authentication.redirect_uri = pytest.placeholders.redirect_uri
        authorizer = prawcore.Authorizer(self.authentication)
        with self.use_cassette():
            authorizer.authorize(pytest.placeholders.temporary_grant_code)
            authorizer.revoke()

        assert authorizer.access_token is None
        assert authorizer.refresh_token is None
        assert authorizer.scopes is None
        assert not authorizer.is_valid()

    def test_revoke__refresh_token_with_access_set(self):
        authorizer = prawcore.Authorizer(
            self.authentication, refresh_token=pytest.placeholders.refresh_token
        )
        with self.use_cassette():
            authorizer.refresh()
            authorizer.revoke()

        assert authorizer.access_token is None
        assert authorizer.refresh_token is None
        assert authorizer.scopes is None
        assert not authorizer.is_valid()

    def test_revoke__refresh_token_without_access_set(self):
        authorizer = prawcore.Authorizer(
            self.authentication, refresh_token=pytest.placeholders.refresh_token
        )
        with self.use_cassette():
            authorizer.revoke()

        assert authorizer.access_token is None
        assert authorizer.refresh_token is None
        assert authorizer.scopes is None
        assert not authorizer.is_valid()


class TestDeviceIDAuthorizer(AuthorizerBase):
    def setup(self):
        super().setup()
        self.authentication = prawcore.UntrustedAuthenticator(
            self.requestor, pytest.placeholders.client_id
        )

    def test_refresh(self):
        authorizer = prawcore.DeviceIDAuthorizer(self.authentication)
        with self.use_cassette():
            authorizer.refresh()

        assert authorizer.access_token is not None
        assert authorizer.scopes == {"*"}
        assert authorizer.is_valid()

    def test_refresh__with_scopes_and_trusted_authenticator(self):
        scope_list = {"adsedit", "adsread", "creddits", "history"}
        authorizer = prawcore.DeviceIDAuthorizer(
            prawcore.TrustedAuthenticator(
                self.requestor,
                pytest.placeholders.client_id,
                pytest.placeholders.client_secret,
            ),
            scopes=scope_list,
        )
        with self.use_cassette():
            authorizer.refresh()

        assert authorizer.access_token is not None
        assert authorizer.scopes == scope_list
        assert authorizer.is_valid()

    def test_refresh__with_short_device_id(self):
        authorizer = prawcore.DeviceIDAuthorizer(self.authentication, "a" * 19)
        with self.use_cassette():
            with pytest.raises(prawcore.OAuthException):
                authorizer.refresh()


class TestReadOnlyAuthorizer(AuthorizerBase):
    def test_refresh(self):
        authorizer = prawcore.ReadOnlyAuthorizer(self.authentication)
        assert authorizer.access_token is None
        assert authorizer.scopes is None
        assert not authorizer.is_valid()

        with self.use_cassette():
            authorizer.refresh()

        assert authorizer.access_token is not None
        assert authorizer.scopes == {"*"}
        assert authorizer.is_valid()

    def test_refresh__with_scopes(self):
        scope_list = {"adsedit", "adsread", "creddits", "history"}
        authorizer = prawcore.ReadOnlyAuthorizer(self.authentication, scopes=scope_list)
        assert authorizer.access_token is None
        assert authorizer.scopes is None
        assert not authorizer.is_valid()

        with self.use_cassette():
            authorizer.refresh()

        assert authorizer.access_token is not None
        assert authorizer.scopes == scope_list
        assert authorizer.is_valid()


class TestScriptAuthorizer(AuthorizerBase):
    def test_refresh(self):
        authorizer = prawcore.ScriptAuthorizer(
            self.authentication,
            pytest.placeholders.username,
            pytest.placeholders.password,
        )
        assert authorizer.access_token is None
        assert authorizer.scopes is None
        assert not authorizer.is_valid()

        with self.use_cassette():
            authorizer.refresh()

        assert authorizer.access_token is not None
        assert authorizer.scopes == {"*"}
        assert authorizer.is_valid()

    def test_refresh__with_invalid_otp(self):
        authorizer = prawcore.ScriptAuthorizer(
            self.authentication,
            pytest.placeholders.username,
            pytest.placeholders.password,
            lambda: "fake",
        )

        with self.use_cassette():
            with pytest.raises(prawcore.OAuthException):
                authorizer.refresh()
        assert not authorizer.is_valid()

    def test_refresh__with_invalid_username_or_password(self):
        authorizer = prawcore.ScriptAuthorizer(
            self.authentication, pytest.placeholders.username, "invalidpassword"
        )
        with self.use_cassette():
            with pytest.raises(prawcore.OAuthException):
                authorizer.refresh()
        assert not authorizer.is_valid()

    def test_refresh__with_scopes(self):
        scope_list = {"adsedit", "adsread", "creddits", "history"}
        authorizer = prawcore.ScriptAuthorizer(
            self.authentication,
            pytest.placeholders.username,
            pytest.placeholders.password,
            scopes=scope_list,
        )
        with self.use_cassette():
            authorizer.refresh()

        assert authorizer.access_token is not None
        assert authorizer.scopes == scope_list
        assert authorizer.is_valid()

    def test_refresh__with_valid_otp(self):
        authorizer = prawcore.ScriptAuthorizer(
            self.authentication,
            pytest.placeholders.username,
            pytest.placeholders.password,
            lambda: "000000",
        )
        assert authorizer.access_token is None
        assert authorizer.scopes is None
        assert not authorizer.is_valid()

        with self.use_cassette():
            authorizer.refresh()

        assert authorizer.access_token is not None
        assert authorizer.scopes == {"*"}
        assert authorizer.is_valid()
