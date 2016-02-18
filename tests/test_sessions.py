"""Test for prawcore.Sessions module."""
import prawcore
import unittest
from .config import CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN, REQUESTOR
from betamax import Betamax
from prawcore.auth import Authorizer


class InvalidAuthorizer(Authorizer):
    def __init__(self):
        super(InvalidAuthorizer, self).__init__(
            prawcore.Authenticator(REQUESTOR, CLIENT_ID, CLIENT_SECRET))

    def is_valid(self):
        return False


def readonly_authorizer(refresh=True):
    authenticator = prawcore.Authenticator(REQUESTOR, CLIENT_ID, CLIENT_SECRET)
    authorizer = prawcore.ReadOnlyAuthorizer(authenticator)
    if refresh:
        authorizer.refresh()
    return authorizer


def valid_authorizer():
    authenticator = prawcore.Authenticator(REQUESTOR, CLIENT_ID, CLIENT_SECRET)
    authorizer = prawcore.Authorizer(authenticator, REFRESH_TOKEN)
    authorizer.refresh()
    return authorizer


class SessionTest(unittest.TestCase):
    def test_close(self):
        prawcore.Session(readonly_authorizer(refresh=False)).close()

    def test_context_manager(self):
        with prawcore.Session(readonly_authorizer(refresh=False)) as session:
            self.assertIsInstance(session, prawcore.Session)

    def test_init__without_authenticator(self):
        self.assertRaises(prawcore.InvalidInvocation, prawcore.Session, None)

    def test_request(self):
        with Betamax(REQUESTOR).use_cassette('Session_request'):
            session = prawcore.Session(readonly_authorizer())
            data = session.request('GET', '/')
        self.assertIsInstance(data, dict)
        self.assertEqual('Listing', data['kind'])

    def test_request__raw_json(self):
        with Betamax(REQUESTOR).use_cassette(
                'Session_request__raw_json'):
            session = prawcore.Session(readonly_authorizer())
            data = session.request('GET', ('/r/reddit_api_test/comments/'
                                           '45xjdr/want_raw_json_test/'))
        self.assertEqual('WANT_RAW_JSON test: < > &',
                         data[0]['data']['children'][0]['data']['title'])

    def test_request__with_insufficent_scope(self):
        with Betamax(REQUESTOR).use_cassette(
                'Session_request__with_insufficient_scope'):
            session = prawcore.Session(valid_authorizer())
            self.assertRaises(prawcore.InsufficientScope, session.request,
                              'GET', '/api/v1/me')

    def test_request__with_invalid_access_token(self):
        with Betamax(REQUESTOR).use_cassette(
                'Session_request__with_invalid_access_token'):
            session = prawcore.Session(readonly_authorizer())
            session._authorizer.access_token += 'invalid'
            self.assertRaises(prawcore.InvalidToken, session.request, 'GET',
                              '/')

    def test_request__with_invalid_authorizer(self):
        session = prawcore.Session(InvalidAuthorizer())
        self.assertRaises(prawcore.InvalidInvocation, session.request,
                          'get', '/')


class SessionFunctionTest(unittest.TestCase):
    def test_session(self):
        self.assertIsInstance(prawcore.session(InvalidAuthorizer()),
                              prawcore.Session)
