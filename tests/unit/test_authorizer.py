"""Test for prawcore.auth.Authorizer classes."""
import pytest

import prawcore

from . import UnitTest


class AuthorizerBase(UnitTest):
    def setup(self):
        super().setup()
        self.authentication = prawcore.TrustedAuthenticator(
            self.requestor,
            pytest.placeholders.client_id,
            pytest.placeholders.client_secret,
        )


class TestAuthorizer(AuthorizerBase):
    def test_authorize__fail_without_redirect_uri(self):
        authorizer = prawcore.Authorizer(self.authentication)
        with pytest.raises(prawcore.InvalidInvocation):
            authorizer.authorize("dummy code")
        assert not authorizer.is_valid()

    def test_initialize(self):
        authorizer = prawcore.Authorizer(self.authentication)
        assert authorizer.access_token is None
        assert authorizer.scopes is None
        assert authorizer.refresh_token is None
        assert not authorizer.is_valid()

    def test_initialize__with_refresh_token(self):
        authorizer = prawcore.Authorizer(
            self.authentication, refresh_token=pytest.placeholders.refresh_token
        )
        assert authorizer.access_token is None
        assert authorizer.scopes is None
        assert pytest.placeholders.refresh_token == authorizer.refresh_token
        assert not authorizer.is_valid()

    def test_initialize__with_untrusted_authenticator(self):
        authenticator = prawcore.UntrustedAuthenticator(None, None)
        authorizer = prawcore.Authorizer(authenticator)
        assert authorizer.access_token is None
        assert authorizer.scopes is None
        assert authorizer.refresh_token is None
        assert not authorizer.is_valid()

    def test_refresh__without_refresh_token(self):
        authorizer = prawcore.Authorizer(self.authentication)
        with pytest.raises(prawcore.InvalidInvocation):
            authorizer.refresh()
        assert not authorizer.is_valid()

    def test_revoke__without_access_token(self):
        authorizer = prawcore.Authorizer(
            self.authentication, refresh_token=pytest.placeholders.refresh_token
        )
        with pytest.raises(prawcore.InvalidInvocation):
            authorizer.revoke(only_access=True)

    def test_revoke__without_any_token(self):
        authorizer = prawcore.Authorizer(self.authentication)
        with pytest.raises(prawcore.InvalidInvocation):
            authorizer.revoke()


class TestDeviceIDAuthorizer(AuthorizerBase):
    def setup(self):
        super().setup()
        self.authentication = prawcore.UntrustedAuthenticator(
            self.requestor, pytest.placeholders.client_id
        )

    def test_initialize(self):
        authorizer = prawcore.DeviceIDAuthorizer(self.authentication)
        assert authorizer.access_token is None
        assert authorizer.scopes is None
        assert not authorizer.is_valid()

    def test_initialize__with_base_authenticator(self):
        authenticator = prawcore.Authorizer(
            prawcore.auth.BaseAuthenticator(None, None, None)
        )
        with pytest.raises(prawcore.InvalidInvocation):
            prawcore.DeviceIDAuthorizer(
                authenticator,
            )


class TestImplicitAuthorizer(AuthorizerBase):
    def test_initialize(self):
        authenticator = prawcore.UntrustedAuthenticator(
            self.requestor, pytest.placeholders.client_id
        )
        authorizer = prawcore.ImplicitAuthorizer(
            authenticator, "fake token", 1, "modposts read"
        )
        assert authorizer.access_token == "fake token"
        assert authorizer.scopes == {"modposts", "read"}
        assert authorizer.is_valid()

    def test_initialize__with_trusted_authenticator(self):
        with pytest.raises(prawcore.InvalidInvocation):
            prawcore.ImplicitAuthorizer(
                self.authentication,
                None,
                None,
                None,
            )


class TestReadOnlyAuthorizer(AuthorizerBase):
    def test_initialize__with_untrusted_authenticator(self):
        authenticator = prawcore.UntrustedAuthenticator(
            self.requestor, pytest.placeholders.client_id
        )
        with pytest.raises(prawcore.InvalidInvocation):
            prawcore.ReadOnlyAuthorizer(
                authenticator,
            )


class TestScriptAuthorizer(AuthorizerBase):
    def test_initialize__with_untrusted_authenticator(self):
        authenticator = prawcore.UntrustedAuthenticator(
            self.requestor, pytest.placeholders.client_id
        )
        with pytest.raises(prawcore.InvalidInvocation):
            prawcore.ScriptAuthorizer(authenticator, None, None)
