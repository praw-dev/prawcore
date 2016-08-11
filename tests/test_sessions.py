"""Test for prawcore.Sessions module."""
from json import dumps

import prawcore
import unittest
from .config import (CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN, REQUESTOR,
                     PASSWORD, USERNAME)
from betamax import Betamax


class InvalidAuthorizer(prawcore.Authorizer):
    def __init__(self):
        super(InvalidAuthorizer, self).__init__(
            prawcore.TrustedAuthenticator(REQUESTOR, CLIENT_ID, CLIENT_SECRET))

    def is_valid(self):
        return False


def client_authorizer():
    authenticator = prawcore.TrustedAuthenticator(REQUESTOR, CLIENT_ID,
                                                  CLIENT_SECRET)
    authorizer = prawcore.Authorizer(authenticator, REFRESH_TOKEN)
    authorizer.refresh()
    return authorizer


def readonly_authorizer(refresh=True):
    authenticator = prawcore.TrustedAuthenticator(REQUESTOR, CLIENT_ID,
                                                  CLIENT_SECRET)
    authorizer = prawcore.ReadOnlyAuthorizer(authenticator)
    if refresh:
        authorizer.refresh()
    return authorizer


def script_authorizer():
    authenticator = prawcore.TrustedAuthenticator(REQUESTOR, CLIENT_ID,
                                                  CLIENT_SECRET)
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

    def test_init__with_device_id_authorizer(self):
        authenticator = prawcore.UntrustedAuthenticator(REQUESTOR, CLIENT_ID)
        authorizer = prawcore.DeviceIDAuthorizer(authenticator)
        prawcore.Session(authorizer)

    def test_init__with_implicit_authorizer(self):
        authenticator = prawcore.UntrustedAuthenticator(REQUESTOR, CLIENT_ID)
        authorizer = prawcore.ImplicitAuthorizer(authenticator, None, 0, '')
        prawcore.Session(authorizer)

    def test_request__get(self):
        with Betamax(REQUESTOR).use_cassette('Session_request__get'):
            session = prawcore.Session(readonly_authorizer())
            response = session.request('GET', '/')
        self.assertIsInstance(response, dict)
        self.assertEqual('Listing', response['kind'])

    def test_request__patch(self):
        with Betamax(REQUESTOR).use_cassette(
                'Session_request__patch',
                match_requests_on=['method', 'uri', 'json-body']):
            session = prawcore.Session(script_authorizer())
            json = {'lang': 'ja', 'num_comments': 123}
            response = session.request('PATCH', '/api/v1/me/prefs', json=json)
            self.assertEqual('ja', response['lang'])
            self.assertEqual(123, response['num_comments'])

    def test_request__post(self):
        with Betamax(REQUESTOR).use_cassette('Session_request__post'):
            session = prawcore.Session(script_authorizer())
            data = {'kind': 'self', 'sr': 'reddit_api_test', 'text': 'Test!',
                    'title': 'A Test from PRAWCORE.'}
            response = session.request('POST', '/api/submit', data=data)
            self.assertIn('a_test_from_prawcore',
                          response['json']['data']['url'])

    def test_request__raw_json(self):
        with Betamax(REQUESTOR).use_cassette('Session_request__raw_json'):
            session = prawcore.Session(readonly_authorizer())
            response = session.request('GET', ('/r/reddit_api_test/comments/'
                                               '45xjdr/want_raw_json_test/'))
        self.assertEqual('WANT_RAW_JSON test: < > &',
                         response[0]['data']['children'][0]['data']['title'])

    def test_request__bad_gateway(self):
        with Betamax(REQUESTOR).use_cassette('Session_request__bad_gateway'):
            session = prawcore.Session(readonly_authorizer())
            with self.assertRaises(prawcore.ServerError) as context_manager:
                session.request('GET', '/')
            self.assertEqual(
                502, context_manager.exception.response.status_code)

    def test_request__bad_request(self):
        with Betamax(REQUESTOR).use_cassette('Session_request__bad_request'):
            session = prawcore.Session(script_authorizer())
            with self.assertRaises(prawcore.BadRequest) as context_manager:
                session.request('PUT', '/api/v1/me/friends/spez',
                                data='{"note": "prawcore"}')
            self.assertIn('reason', context_manager.exception.response.json())

    def test_request__cloudflair_connection_timed_out(self):
        with Betamax(REQUESTOR).use_cassette(
                'Session_request__cloudflair_connection_timed_out'):
            session = prawcore.Session(readonly_authorizer())
            with self.assertRaises(prawcore.ServerError) as context_manager:
                session.request('GET', '/')
                session.request('GET', '/')
                session.request('GET', '/')
            self.assertEqual(
                522, context_manager.exception.response.status_code)

    def test_request__created(self):
        with Betamax(REQUESTOR).use_cassette('Session_request__created'):
            session = prawcore.Session(script_authorizer())
            response = session.request('PUT', '/api/v1/me/friends/spez',
                                       data='{}')
            self.assertIn('name', response)

    def test_request__forbidden(self):
        with Betamax(REQUESTOR).use_cassette('Session_request__forbidden'):
            session = prawcore.Session(script_authorizer())
            self.assertRaises(prawcore.Forbidden, session.request,
                              'GET', '/user/spez/gilded/given')

    def test_request__gateway_timeout(self):
        with Betamax(REQUESTOR).use_cassette(
                'Session_request__gateway_timeout'):
            session = prawcore.Session(readonly_authorizer())
            with self.assertRaises(prawcore.ServerError) as context_manager:
                session.request('GET', '/')
            self.assertEqual(
                504, context_manager.exception.response.status_code)

    def test_request__no_content(self):
        with Betamax(REQUESTOR).use_cassette('Session_request__no_content'):
            session = prawcore.Session(script_authorizer())
            response = session.request('DELETE', '/api/v1/me/friends/spez')
            self.assertIsNone(response)

    def test_request__not_found(self):
        with Betamax(REQUESTOR).use_cassette('Session_request__not_found'):
            session = prawcore.Session(script_authorizer())
            self.assertRaises(prawcore.NotFound, session.request,
                              'GET', '/r/reddit_api_test/wiki/invalid')

    def test_request__okay_with_0_byte_content(self):
        with Betamax(REQUESTOR).use_cassette(
                'Session_request__okay_with_0_byte_content'):
            session = prawcore.Session(script_authorizer())
            data = {'model': dumps({'name': 'redditdev'})}
            path = '/api/multi/user/{}/m/praw_x5g968f66a/r/redditdev'.format(
                USERNAME)
            response = session.request('DELETE', path, data=data)
            self.assertEqual('', response)

    def test_request__redirect(self):
        with Betamax(REQUESTOR).use_cassette('Session_request__redirect'):
            session = prawcore.Session(readonly_authorizer())
            with self.assertRaises(prawcore.Redirect) as context_manager:
                session.request('GET', '/r/random')
            self.assertTrue(context_manager.exception.path.startswith('/r/'))

    def test_request__service_unavailable(self):
        with Betamax(REQUESTOR).use_cassette(
                'Session_request__service_unavailable'):
            session = prawcore.Session(readonly_authorizer())
            with self.assertRaises(prawcore.ServerError) as context_manager:
                session.request('GET', '/')
                session.request('GET', '/')
                session.request('GET', '/')
            self.assertEqual(
                503, context_manager.exception.response.status_code)

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
