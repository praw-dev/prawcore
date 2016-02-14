"""Test for prawcore.auth.Authorizer classes."""
from betamax import Betamax
import prawcore
import unittest
from .config import CLIENT_ID, CLIENT_SECRET, PASSWORD, REFRESH_TOKEN, USERNAME


class AuthorizerTest(unittest.TestCase):
    def setUp(self):
        self.authentication = prawcore.Authenticator(CLIENT_ID, CLIENT_SECRET)

    def test_refresh(self):
        authorizer = prawcore.Authorizer(self.authentication, REFRESH_TOKEN)
        self.assertIsNone(authorizer.access_token)
        self.assertIsNone(authorizer.scopes)
        self.assertFalse(authorizer.is_valid())

        with Betamax(authorizer._session).use_cassette('Authorizer_refresh'):
            authorizer.refresh()

        self.assertIsNotNone(authorizer.access_token)
        self.assertIsInstance(authorizer.scopes, set)
        self.assertTrue(len(authorizer.scopes) > 0)
        self.assertTrue(authorizer.is_valid())

    def test_refresh__with_invalid_token(self):
        authorizer = prawcore.Authorizer(self.authentication, 'INVALID_TOKEN')
        with Betamax(authorizer._session).use_cassette(
                'Authorizer_refresh__with_invalid_token'):
            self.assertRaises(prawcore.RequestException, authorizer.refresh)
            self.assertFalse(authorizer.is_valid())

    def test_refresh__without_refresh_token(self):
        authorizer = prawcore.Authorizer(self.authentication)
        self.assertRaises(prawcore.InvalidInvocation, authorizer.refresh)
        self.assertFalse(authorizer.is_valid())


class ReadOnlyAuthorizerTest(AuthorizerTest):
    def test_refresh(self):
        authorizer = prawcore.ReadOnlyAuthorizer(self.authentication)
        self.assertIsNone(authorizer.access_token)
        self.assertIsNone(authorizer.scopes)
        self.assertFalse(authorizer.is_valid())

        with Betamax(authorizer._session).use_cassette(
                'ReadOnlyAuthorizer_refresh'):
            authorizer.refresh()

        self.assertIsNotNone(authorizer.access_token)
        self.assertEqual(set(['*']), authorizer.scopes)
        self.assertTrue(authorizer.is_valid())


class ScriptAuthorizerTest(AuthorizerTest):
    def test_refresh(self):
        authorizer = prawcore.ScriptAuthorizer(self.authentication, USERNAME,
                                               PASSWORD)
        self.assertIsNone(authorizer.access_token)
        self.assertIsNone(authorizer.scopes)
        self.assertFalse(authorizer.is_valid())

        with Betamax(authorizer._session).use_cassette(
                'ScriptAuthorizer_refresh'):
            authorizer.refresh()

        self.assertIsNotNone(authorizer.access_token)
        self.assertEqual(set(['*']), authorizer.scopes)
        self.assertTrue(authorizer.is_valid())

    def test_refresh__with_invalid_username_or_password(self):
        authorizer = prawcore.ScriptAuthorizer(self.authentication, USERNAME,
                                               'invalidpassword')
        with Betamax(authorizer._session).use_cassette(
                'ScriptAuthorizer_refresh__with_invalid_username_or_password'):
            self.assertRaises(prawcore.OAuthException, authorizer.refresh)
            self.assertFalse(authorizer.is_valid())
