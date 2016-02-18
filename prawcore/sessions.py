"""prawcore.sessions: Provides prawcore.Session and prawcore.session."""
from .auth import Authorizer
from .rate_limit import RateLimiter
from .exceptions import InvalidInvocation
from .util import authorization_error_class
from requests.status_codes import codes


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

    def request(self, method, path):
        """Return the json content from the resource at ``path``.

        :param path: The path of the request. This path will be combined with
            the ``oauth_url`` of the Requestor.

        """
        if not self._authorizer.is_valid():
            raise InvalidInvocation('authorizer does not have a valid token')

        headers = {'Authorization': 'bearer {}'
                   .format(self._authorizer.access_token)}
        params = {'raw_json': '1'}
        url = self._requestor.oauth_url + path
        response = self._rate_limiter.call(self._requestor._http.request,
                                           method, url, headers=headers,
                                           params=params)

        if response.status_code in (codes['forbidden'], codes['unauthorized']):
            raise authorization_error_class(response)
        assert response.status_code == codes['ok'], \
            'Unexpected status code: {}'.format(response.status_code)
        return response.json()


def session(authorizer=None):
    """Return a :class:`Session` instance.

    :param authorizer: An instance of :class:`Authorizer`.

    """
    return Session(authorizer=authorizer)
