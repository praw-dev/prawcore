"""Test for prawcore.auth.Authenticator class."""
import prawcore
import unittest
from .config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI


class AuthenticatorTest(unittest.TestCase):
    def test_authorize_url(self):
        auth = prawcore.Authenticator(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)
        url = auth.authorize_url('permanent', ['identity', 'read'], 'a_state')
        self.assertIn('client_id={}'.format(CLIENT_ID), url)
        self.assertIn('duration=permanent', url)
        self.assertIn('scope=identity+read', url)
        self.assertIn('state=a_state', url)

    def test_authorize_url__fail_without_redirect_uri(self):
        auth = prawcore.Authenticator(CLIENT_ID, CLIENT_SECRET)
        self.assertRaises(prawcore.InvalidInvocation, auth.authorize_url,
                          'permanent', ['identity'], '...')
