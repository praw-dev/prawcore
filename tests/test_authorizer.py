"""Test for prawcore.auth.Authorizer class."""
from betamax import Betamax
import prawcore
import time
import unittest
from .config import CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN


class AuthorizerTest(unittest.TestCase):
    def setUp(self):
        self.authentication = prawcore.Authenticator(CLIENT_ID, CLIENT_SECRET)

    def test_refresh(self):
        authorizer = prawcore.Authorizer(self.authentication, REFRESH_TOKEN)
        self.assertIsNone(authorizer.access_token)
        self.assertIsNone(authorizer.expiration)
        self.assertIsNone(authorizer.scopes)

        with Betamax(authorizer._session).use_cassette('Authorizer_refresh'):
            authorizer.refresh()

        self.assertIsNotNone(authorizer.access_token)
        self.assertTrue(authorizer.expiration > time.time())
        self.assertIsInstance(authorizer.scopes, set)
        self.assertTrue(len(authorizer.scopes) > 0)

    def test_refresh__without_refresh_token(self):
        authorizer = prawcore.Authorizer(self.authentication)
        self.assertRaises(prawcore.InvalidInvocation, authorizer.refresh)
