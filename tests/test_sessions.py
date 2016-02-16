"""Test for prawcore.Sessions module."""
import prawcore
import unittest
from .config import CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN
from betamax import Betamax


class InvalidAuthorizer(object):
    def is_valid(self):
        return False


def readonly_authorizer():
    authenticator = prawcore.Authenticator(CLIENT_ID, CLIENT_SECRET)
    authorizer = prawcore.ReadOnlyAuthorizer(authenticator)
    authorizer.refresh()
    return authorizer


def valid_authorizer():
    authenticator = prawcore.Authenticator(CLIENT_ID, CLIENT_SECRET)
    authorizer = prawcore.Authorizer(authenticator, REFRESH_TOKEN)
    authorizer.refresh()
    return authorizer


class SessionTest(unittest.TestCase):
    def setUp(self):
        self.session = prawcore.Session()

    def test_close(self):
        self.session.close()

    def test_context_manager(self):
        with self.session as session:
            self.assertIsInstance(session, prawcore.Session)

    def test_request(self):
        with Betamax(prawcore.util.http).use_cassette(
                'Session_request'):
            self.session.authorizer = readonly_authorizer()
            data = self.session.request('GET', 'https://oauth.reddit.com')
        self.assertIsInstance(data, dict)
        self.assertEqual('Listing', data['kind'])

    def test_request__raw_json(self):
        with Betamax(prawcore.util.http).use_cassette(
                'Session_request__raw_json'):
            self.session.authorizer = readonly_authorizer()
            data = self.session.request(
                'GET', ('https://oauth.reddit.com/r/reddit'
                        '_api_test/comments/45xjdr/want_raw_json_test/'))
        self.assertEqual('WANT_RAW_JSON test: < > &',
                         data[0]['data']['children'][0]['data']['title'])

    def test_request__with_insufficent_scope(self):
        with Betamax(prawcore.util.http).use_cassette(
                'Session_request__with_insufficient_scope'):
            self.session.authorizer = valid_authorizer()
            self.assertRaises(prawcore.InsufficientScope, self.session.request,
                              'GET', 'https://oauth.reddit.com/api/v1/me')

    def test_request__with_invalid_access_token(self):
        with Betamax(prawcore.util.http).use_cassette(
                'Session_request__with_invalid_access_token'):
            self.session.authorizer = readonly_authorizer()
            self.session.authorizer.access_token += 'invalid'
            self.assertRaises(prawcore.InvalidToken, self.session.request,
                              'GET', 'https://oauth.reddit.com')

    def test_request__with_invalid_authorizer(self):
        self.session.authorizer = InvalidAuthorizer()
        self.assertRaises(prawcore.InvalidInvocation, self.session.request,
                          'get', '')

    def test_request__without_authorizer(self):
        self.assertRaises(prawcore.InvalidInvocation, self.session.request,
                          'get', '')


class SessionFunctionTest(unittest.TestCase):
    def test_session(self):
        self.assertIsInstance(prawcore.session(), prawcore.Session)
