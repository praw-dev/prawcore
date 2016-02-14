"""Test for prawcore.auth.Authorizer classes."""
import prawcore
import unittest
from .config import (CLIENT_ID, CLIENT_SECRET, PASSWORD, PERMANENT_GRANT_CODE,
                     REDIRECT_URI, REFRESH_TOKEN, TEMPORARY_GRANT_CODE,
                     USERNAME)
from betamax import Betamax


class AuthorizerTestBase(unittest.TestCase):
    def setUp(self):
        self.authentication = prawcore.Authenticator(CLIENT_ID, CLIENT_SECRET)


class AuthorizerTest(AuthorizerTestBase):
    def test_authorize__with_permanent_grant(self):
        self.authentication.redirect_uri = REDIRECT_URI
        authorizer = prawcore.Authorizer(self.authentication)
        self.assertIsNone(authorizer.access_token)
        self.assertIsNone(authorizer.scopes)
        self.assertFalse(authorizer.is_valid())

        with Betamax(self.authentication._session).use_cassette(
                'Authorizer_authorize__with_permanent_grant'):
            authorizer.authorize(PERMANENT_GRANT_CODE)

        self.assertIsNotNone(authorizer.access_token)
        self.assertIsNotNone(authorizer.refresh_token)
        self.assertIsInstance(authorizer.scopes, set)
        self.assertTrue(len(authorizer.scopes) > 0)
        self.assertTrue(authorizer.is_valid())

    def test_authorize__with_temporary_grant(self):
        self.authentication.redirect_uri = REDIRECT_URI
        authorizer = prawcore.Authorizer(self.authentication)
        self.assertIsNone(authorizer.access_token)
        self.assertIsNone(authorizer.scopes)
        self.assertFalse(authorizer.is_valid())

        with Betamax(self.authentication._session).use_cassette(
                'Authorizer_authorize__with_temporary_grant'):
            authorizer.authorize(TEMPORARY_GRANT_CODE)

        self.assertIsNotNone(authorizer.access_token)
        self.assertIsNone(authorizer.refresh_token)
        self.assertIsInstance(authorizer.scopes, set)
        self.assertTrue(len(authorizer.scopes) > 0)
        self.assertTrue(authorizer.is_valid())

    def test_authorize__with_invalid_code(self):
        self.authentication.redirect_uri = REDIRECT_URI
        authorizer = prawcore.Authorizer(self.authentication)
        with Betamax(self.authentication._session).use_cassette(
                'Authorizer_authorize__with_invalid_code'):
            self.assertRaises(prawcore.OAuthException, authorizer.authorize,
                              'invalid code')
        self.assertFalse(authorizer.is_valid())

    def test_authorize__fail_without_redirect_uri(self):
        authorizer = prawcore.Authorizer(self.authentication)
        self.assertRaises(prawcore.InvalidInvocation, authorizer.authorize,
                          'dummy code')
        self.assertFalse(authorizer.is_valid())

    def test_refresh(self):
        authorizer = prawcore.Authorizer(self.authentication, REFRESH_TOKEN)
        self.assertIsNone(authorizer.access_token)
        self.assertIsNone(authorizer.scopes)
        self.assertFalse(authorizer.is_valid())

        with Betamax(self.authentication._session).use_cassette(
                'Authorizer_refresh'):
            authorizer.refresh()

        self.assertIsNotNone(authorizer.access_token)
        self.assertIsInstance(authorizer.scopes, set)
        self.assertTrue(len(authorizer.scopes) > 0)
        self.assertTrue(authorizer.is_valid())

    def test_refresh__with_invalid_token(self):
        authorizer = prawcore.Authorizer(self.authentication, 'INVALID_TOKEN')
        with Betamax(self.authentication._session).use_cassette(
                'Authorizer_refresh__with_invalid_token'):
            self.assertRaises(prawcore.RequestException, authorizer.refresh)
            self.assertFalse(authorizer.is_valid())

    def test_refresh__without_refresh_token(self):
        authorizer = prawcore.Authorizer(self.authentication)
        self.assertRaises(prawcore.InvalidInvocation, authorizer.refresh)
        self.assertFalse(authorizer.is_valid())


class ReadOnlyAuthorizerTest(AuthorizerTestBase):
    def test_refresh(self):
        authorizer = prawcore.ReadOnlyAuthorizer(self.authentication)
        self.assertIsNone(authorizer.access_token)
        self.assertIsNone(authorizer.scopes)
        self.assertFalse(authorizer.is_valid())

        with Betamax(self.authentication._session).use_cassette(
                'ReadOnlyAuthorizer_refresh'):
            authorizer.refresh()

        self.assertIsNotNone(authorizer.access_token)
        self.assertEqual(set(['*']), authorizer.scopes)
        self.assertTrue(authorizer.is_valid())


class ScriptAuthorizerTest(AuthorizerTestBase):
    def test_refresh(self):
        authorizer = prawcore.ScriptAuthorizer(self.authentication, USERNAME,
                                               PASSWORD)
        self.assertIsNone(authorizer.access_token)
        self.assertIsNone(authorizer.scopes)
        self.assertFalse(authorizer.is_valid())

        with Betamax(self.authentication._session).use_cassette(
                'ScriptAuthorizer_refresh'):
            authorizer.refresh()

        self.assertIsNotNone(authorizer.access_token)
        self.assertEqual(set(['*']), authorizer.scopes)
        self.assertTrue(authorizer.is_valid())

    def test_refresh__with_invalid_username_or_password(self):
        authorizer = prawcore.ScriptAuthorizer(self.authentication, USERNAME,
                                               'invalidpassword')
        with Betamax(self.authentication._session).use_cassette(
                'ScriptAuthorizer_refresh__with_invalid_username_or_password'):
            self.assertRaises(prawcore.OAuthException, authorizer.refresh)
            self.assertFalse(authorizer.is_valid())
