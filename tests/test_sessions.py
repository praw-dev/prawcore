"""Test for prawcore.Sessions module."""
import prawcore
import unittest
from .config import (CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN, REQUESTOR,
                     PASSWORD, USERNAME)
from betamax import Betamax
from prawcore.auth import Authorizer


class InvalidAuthorizer(Authorizer):
    def __init__(self):
        super(InvalidAuthorizer, self).__init__(
            prawcore.Authenticator(REQUESTOR, CLIENT_ID, CLIENT_SECRET))

    def is_valid(self):
        return False


def client_authorizer():
    authenticator = prawcore.Authenticator(REQUESTOR, CLIENT_ID, CLIENT_SECRET)
    authorizer = prawcore.Authorizer(authenticator, REFRESH_TOKEN)
    authorizer.refresh()
    return authorizer


def readonly_authorizer(refresh=True):
    authenticator = prawcore.Authenticator(REQUESTOR, CLIENT_ID, CLIENT_SECRET)
    authorizer = prawcore.ReadOnlyAuthorizer(authenticator)
    if refresh:
        authorizer.refresh()
    return authorizer


def script_authorizer():
    authenticator = prawcore.Authenticator(REQUESTOR, CLIENT_ID, CLIENT_SECRET)
    authorizer = prawcore.ScriptAuthorizer(authenticator, USERNAME, PASSWORD)
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

    def test_request__get(self):
        with Betamax(REQUESTOR).use_cassette('Session_request__get'):
            session = prawcore.Session(readonly_authorizer())
            response = session.request('GET', '/')
        self.assertIsInstance(response, dict)
        self.assertEqual('Listing', response['kind'])

    def test_request__post(self):
        with Betamax(REQUESTOR).use_cassette(
                'Session_request__post'):
            session = prawcore.Session(script_authorizer())
            data = {'kind': 'self', 'sr': 'reddit_api_test', 'text': 'Test!',
                    'title': 'A Test from PRAWCORE.'}
            response = session.request('POST', '/api/submit', data=data)
            self.assertIn('a_test_from_prawcore',
                          response['json']['data']['url'])

    def test_request__raw_json(self):
        with Betamax(REQUESTOR).use_cassette(
                'Session_request__raw_json'):
            session = prawcore.Session(readonly_authorizer())
            response = session.request('GET', ('/r/reddit_api_test/comments/'
                                               '45xjdr/want_raw_json_test/'))
        self.assertEqual('WANT_RAW_JSON test: < > &',
                         response[0]['data']['children'][0]['data']['title'])

    def test_request__created(self):
        with Betamax(REQUESTOR).use_cassette(
                'Session_request__created'):
            session = prawcore.Session(script_authorizer())
            response = session.request('PUT', '/api/v1/me/friends/spez',
                                       data='{}')
            self.assertIn('name', response)

    def test_request__forbidden(self):
        with Betamax(REQUESTOR).use_cassette(
                'Session_request__forbidden'):
            session = prawcore.Session(script_authorizer())
            self.assertRaises(prawcore.Forbidden, session.request,
                              'GET', '/user/spez/gilded/given')

    def test_request__redirect(self):
        with Betamax(REQUESTOR).use_cassette(
                'Session_request__redirect'):
            session = prawcore.Session(readonly_authorizer())
            with self.assertRaises(prawcore.Redirect) as context_manager:
                session.request('GET', '/r/random')
            self.assertTrue(context_manager.exception.path.startswith('/r/'))

    def test_request__with_insufficent_scope(self):
        with Betamax(REQUESTOR).use_cassette(
                'Session_request__with_insufficient_scope'):
            session = prawcore.Session(client_authorizer())
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
