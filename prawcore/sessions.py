"""prawcore.sessions: Provides prawcore.Session and prawcore.session."""
import logging

from requests.compat import urljoin
from requests.status_codes import codes

from .auth import Authorizer
from .rate_limit import RateLimiter
from .exceptions import InvalidInvocation, Redirect
from .util import authorization_error_class

log = logging.getLogger(__package__)


class Session(object):
    """The low-level connection interface to reddit's API."""

    def __init__(self, authorizer):
        """Preprare the connection to reddit's API.

        :param authorizer: An instance of :class:`Authorizer`.

        """
        if not isinstance(authorizer, Authorizer):
            raise InvalidInvocation('invalid Authorizer: {}'
                                    .format(authorizer))
        self._authorizer = authorizer
        self._rate_limiter = RateLimiter()

    def __enter__(self):
        """Allow this object to be used as a context manager."""
        return self

    def __exit__(self, *_args):
        """Allow this object to be used as a context manager."""
        self.close()

    @property
    def _requestor(self):
        return self._authorizer._authenticator._requestor

    def close(self):
        """Close the session and perform any clean up."""
        self._requestor._http.close()

    def request(self, method, path, params=None, data=None):
        """Return the json content from the resource at ``path``.

        :param method: The request verb. E.g., get, post, put.
        :param path: The path of the request. This path will be combined with
            the ``oauth_url`` of the Requestor.
        :param params: The query parameters to send with the request.
        :param data: Dictionary, bytes, or file-like object to send in the body
            of the request.

        """
        if not self._authorizer.is_valid():
            raise InvalidInvocation('authorizer does not have a valid token')

        headers = {'Authorization': 'bearer {}'
                   .format(self._authorizer.access_token)}
        params = params or {}
        params['raw_json'] = 1
        if isinstance(data, dict):
            data['api_type'] = 'json'
            data = sorted(data.items())
        url = urljoin(self._requestor.oauth_url, path)

        log.debug('Fetching: {} {}'.format(method, url))
        log.debug('Headers: {}'.format(headers))
        log.debug('Params: {}'.format(params))
        log.debug('Data: {}'.format(data))

        response = self._rate_limiter.call(self._requestor._http.request,
                                           method, url, allow_redirects=False,
                                           data=data, headers=headers,
                                           params=params)

        log.debug('Response: {} ({} bytes)'.format(
            response.status_code, response.headers.get('content-length')))

        if response.status_code in (codes['forbidden'], codes['unauthorized']):
            raise authorization_error_class(response)
        elif response.status_code == codes['found']:
            raise Redirect(response)
        assert response.status_code in (codes['created'], codes['ok']), \
            'Unexpected status code: {}'.format(response.status_code)
        return response.json()


def session(authorizer=None):
    """Return a :class:`Session` instance.

    :param authorizer: An instance of :class:`Authorizer`.

    """
    return Session(authorizer=authorizer)
