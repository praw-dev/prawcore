"""Test for prawcore.auth.Authenticator class."""
import prawcore
import unittest
from .config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, REQUESTOR
from betamax import Betamax


class AuthenticatorTest(unittest.TestCase):
    def test_authorize_url(self):
        authenticator = prawcore.Authenticator(CLIENT_ID, CLIENT_SECRET,
                                               REDIRECT_URI)
        url = authenticator.authorize_url('permanent', ['identity', 'read'],
                                          'a_state')
        self.assertIn('client_id={}'.format(CLIENT_ID), url)
        self.assertIn('duration=permanent', url)
        self.assertIn('scope=identity+read', url)
        self.assertIn('state=a_state', url)

    def test_authorize_url__fail_without_redirect_uri(self):
        authenticator = prawcore.Authenticator(CLIENT_ID, CLIENT_SECRET)
        self.assertRaises(prawcore.InvalidInvocation,
                          authenticator.authorize_url, 'permanent',
                          ['identity'], '...')

    def test_revoke_token(self):
        authenticator = prawcore.Authenticator(CLIENT_ID, CLIENT_SECRET,
                                               requestor=REQUESTOR)
        with Betamax(REQUESTOR).use_cassette('Authenticator_revoke_token'):
            authenticator.revoke_token('dummy token')

    def test_revoke_token__with_access_token_hint(self):
        authenticator = prawcore.Authenticator(CLIENT_ID, CLIENT_SECRET,
                                               requestor=REQUESTOR)
        with Betamax(REQUESTOR).use_cassette(
                'Authenticator_revoke_token__with_access_token_hint'):
            authenticator.revoke_token('dummy token', 'access_token')

    def test_revoke_token__with_refresh_token_hint(self):
        authenticator = prawcore.Authenticator(CLIENT_ID, CLIENT_SECRET,
                                               requestor=REQUESTOR)
        with Betamax(REQUESTOR).use_cassette(
                'Authenticator_revoke_token__with_refresh_token_hint'):
            authenticator.revoke_token('dummy token', 'refresh_token')

    def test_revoke_token__without_requestor(self):
        authenticator = prawcore.Authenticator(CLIENT_ID, CLIENT_SECRET)
        self.assertRaises(prawcore.InvalidInvocation,
                          authenticator.revoke_token, 'dummy token')
