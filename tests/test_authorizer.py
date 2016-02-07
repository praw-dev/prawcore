"""Test for prawcore.auth.Authorizer class."""
from betamax import Betamax
import prawcore
import unittest
from .config import CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN


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
