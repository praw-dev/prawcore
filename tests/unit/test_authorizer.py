"""Test for prawcore.auth.Authorizer classes."""

import pytest

import prawcore

from . import UnitTest


class InvalidAuthenticator(prawcore.auth.BaseAuthenticator):
    def _auth(self):
        pass


class TestAuthorizer(UnitTest):
    def test_authorize__fail_without_redirect_uri(self, trusted_authenticator):
        authorizer = prawcore.Authorizer(trusted_authenticator)
        with pytest.raises(prawcore.InvalidInvocation):
            authorizer.authorize("dummy code")
        assert not authorizer.is_valid()

    def test_initialize(self, trusted_authenticator):
        authorizer = prawcore.Authorizer(trusted_authenticator)
        assert authorizer.access_token is None
        assert authorizer.scopes is None
        assert authorizer.refresh_token is None
        assert not authorizer.is_valid()

    def test_initialize__with_refresh_token(self, trusted_authenticator):
        authorizer = prawcore.Authorizer(
            trusted_authenticator, refresh_token=pytest.placeholders.refresh_token
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

    def test_refresh__without_refresh_token(self, trusted_authenticator):
        authorizer = prawcore.Authorizer(trusted_authenticator)
        with pytest.raises(prawcore.InvalidInvocation):
            authorizer.refresh()
        assert not authorizer.is_valid()

    def test_revoke__without_access_token(self, trusted_authenticator):
        authorizer = prawcore.Authorizer(
            trusted_authenticator, refresh_token=pytest.placeholders.refresh_token
        )
        with pytest.raises(prawcore.InvalidInvocation):
            authorizer.revoke(only_access=True)

    def test_revoke__without_any_token(self, trusted_authenticator):
        authorizer = prawcore.Authorizer(trusted_authenticator)
        with pytest.raises(prawcore.InvalidInvocation):
            authorizer.revoke()


class TestDeviceIDAuthorizer(UnitTest):
    def test_initialize(self, untrusted_authenticator):
        authorizer = prawcore.DeviceIDAuthorizer(untrusted_authenticator)
        assert authorizer.access_token is None
        assert authorizer.scopes is None
        assert not authorizer.is_valid()

    def test_initialize__with_invalid_authenticator(self):
        authenticator = prawcore.Authorizer(InvalidAuthenticator(None, None, None))
        with pytest.raises(prawcore.InvalidInvocation):
            prawcore.DeviceIDAuthorizer(authenticator)


class TestImplicitAuthorizer(UnitTest):
    def test_initialize(self, untrusted_authenticator):
        authorizer = prawcore.ImplicitAuthorizer(
            untrusted_authenticator, "fake token", 1, "modposts read"
        )
        assert authorizer.access_token == "fake token"
        assert authorizer.scopes == {"modposts", "read"}
        assert authorizer.is_valid()

    def test_initialize__with_trusted_authenticator(self, trusted_authenticator):
        with pytest.raises(prawcore.InvalidInvocation):
            prawcore.ImplicitAuthorizer(trusted_authenticator, None, None, None)


class TestReadOnlyAuthorizer(UnitTest):
    def test_initialize__with_untrusted_authenticator(self, untrusted_authenticator):
        with pytest.raises(prawcore.InvalidInvocation):
            prawcore.ReadOnlyAuthorizer(untrusted_authenticator)


class TestScriptAuthorizer(UnitTest):
    def test_initialize__with_untrusted_authenticator(self, untrusted_authenticator):
        with pytest.raises(prawcore.InvalidInvocation):
            prawcore.ScriptAuthorizer(untrusted_authenticator, None, None)
