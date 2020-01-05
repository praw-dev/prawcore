"""Test for sublcasses of prawcore.auth.BaseAuthenticator class."""
import prawcore
import unittest
from .conftest import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, REQUESTOR
from betamax import Betamax


class TrustedAuthenticatorTest(unittest.TestCase):
    def test_authorize_url(self):
        authenticator = prawcore.TrustedAuthenticator(
            REQUESTOR, CLIENT_ID, CLIENT_SECRET, REDIRECT_URI
        )
        url = authenticator.authorize_url(
            "permanent", ["identity", "read"], "a_state"
        )
        self.assertIn("client_id={}".format(CLIENT_ID), url)
        self.assertIn("duration=permanent", url)
        self.assertIn("response_type=code", url)
        self.assertIn("scope=identity+read", url)
        self.assertIn("state=a_state", url)

    def test_authorize_url__fail_with_implicit(self):
        authenticator = prawcore.TrustedAuthenticator(
            REQUESTOR, CLIENT_ID, CLIENT_SECRET, REDIRECT_URI
        )
        self.assertRaises(
            prawcore.InvalidInvocation,
            authenticator.authorize_url,
            "temporary",
            ["identity", "read"],
            "a_state",
            implicit=True,
        )

    def test_authorize_url__fail_without_redirect_uri(self):
        authenticator = prawcore.TrustedAuthenticator(
            REQUESTOR, CLIENT_ID, CLIENT_SECRET
        )
        self.assertRaises(
            prawcore.InvalidInvocation,
            authenticator.authorize_url,
            "permanent",
            ["identity"],
            "...",
        )

    def test_revoke_token(self):
        authenticator = prawcore.TrustedAuthenticator(
            REQUESTOR, CLIENT_ID, CLIENT_SECRET
        )
        with Betamax(REQUESTOR).use_cassette(
            "TrustedAuthenticator_revoke_token"
        ):
            authenticator.revoke_token("dummy token")

    def test_revoke_token__with_access_token_hint(self):
        authenticator = prawcore.TrustedAuthenticator(
            REQUESTOR, CLIENT_ID, CLIENT_SECRET
        )
        with Betamax(REQUESTOR).use_cassette(
            "TrustedAuthenticator_revoke_token__with_access_token_hint"
        ):
            authenticator.revoke_token("dummy token", "access_token")

    def test_revoke_token__with_refresh_token_hint(self):
        authenticator = prawcore.TrustedAuthenticator(
            REQUESTOR, CLIENT_ID, CLIENT_SECRET
        )
        with Betamax(REQUESTOR).use_cassette(
            "TrustedAuthenticator_revoke_token__with_refresh_token_hint"
        ):
            authenticator.revoke_token("dummy token", "refresh_token")


class UntrustedAuthenticatorTest(unittest.TestCase):
    def test_authorize_url__code(self):
        authenticator = prawcore.UntrustedAuthenticator(
            REQUESTOR, CLIENT_ID, REDIRECT_URI
        )
        url = authenticator.authorize_url(
            "permanent", ["identity", "read"], "a_state"
        )
        self.assertIn("client_id={}".format(CLIENT_ID), url)
        self.assertIn("duration=permanent", url)
        self.assertIn("response_type=code", url)
        self.assertIn("scope=identity+read", url)
        self.assertIn("state=a_state", url)

    def test_authorize_url__token(self):
        authenticator = prawcore.UntrustedAuthenticator(
            REQUESTOR, CLIENT_ID, REDIRECT_URI
        )
        url = authenticator.authorize_url(
            "temporary", ["identity", "read"], "a_state", implicit=True
        )
        self.assertIn("client_id={}".format(CLIENT_ID), url)
        self.assertIn("duration=temporary", url)
        self.assertIn("response_type=token", url)
        self.assertIn("scope=identity+read", url)
        self.assertIn("state=a_state", url)

    def test_authorize_url__fail_with_token_and_permanent(self):
        authenticator = prawcore.UntrustedAuthenticator(
            REQUESTOR, CLIENT_ID, REDIRECT_URI
        )
        self.assertRaises(
            prawcore.InvalidInvocation,
            authenticator.authorize_url,
            "permanent",
            ["identity", "read"],
            "a_state",
            implicit=True,
        )

    def test_authorize_url__fail_without_redirect_uri(self):
        authenticator = prawcore.UntrustedAuthenticator(REQUESTOR, CLIENT_ID)
        self.assertRaises(
            prawcore.InvalidInvocation,
            authenticator.authorize_url,
            "temporary",
            ["identity"],
            "...",
        )

    def test_revoke_token(self):
        authenticator = prawcore.UntrustedAuthenticator(REQUESTOR, CLIENT_ID)
        with Betamax(REQUESTOR).use_cassette(
            "UntrustedAuthenticator_revoke_token"
        ):
            authenticator.revoke_token("dummy token")
