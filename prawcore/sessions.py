"""prawcore.sessions: Provides prawcore.Session and prawcore.session."""
from . import util
from .exceptions import InvalidInvocation, RequestException
from .util import authorization_error_class
from requests.status_codes import codes


class Session(object):
    """The low-level connection interface to reddit's API."""

    def __init__(self, authorizer=None):
        """Preprare the connection to reddit's API.

        :param authorizer: An instance of :class:`Authorizer`.

        """
        self.authorizer = authorizer
        self._session = util.http

    def __enter__(self):
        """Allow this object to be used as a context manager."""
        return self

    def __exit__(self, *_args):
        """Allow this object to be used as a context manager."""
        self.close()

    def close(self):
        """Close the session and perform any clean up."""
        self._session.close()

    def request(self, method, url):
        """Return the json content from the resource at ``url``.

        :param url: The URL of the request.

        """
        if self.authorizer is None:
            raise InvalidInvocation('authorizer has not been set')
        elif not self.authorizer.is_valid():
            raise InvalidInvocation('authorizer does not have a valid token')

        headers = {'Authorization': 'bearer {}'
                   .format(self.authorizer.access_token)}
        response = self._session.request(method, url, headers=headers)

        if response.status_code in (codes['forbidden'], codes['unauthorized']):
            raise authorization_error_class(response)
        if response.status_code != codes['ok']:
            raise RequestException(response)


def session(authorizer=None):
    """Return a :class:`Session` instance.

    :param authorizer: An instance of :class:`Authorizer`.

    """
    return Session(authorizer=authorizer)
