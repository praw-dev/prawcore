"""Provide exception classes for the prawcore package."""

import sys


if sys.version_info[0] == 2:
    from urlparse import urlparse
else:
    from urllib.parse import urlparse


class PrawcoreException(Exception):
    """Base exception class for exceptions that occur within this package."""


class InvalidInvocation(PrawcoreException):
    """Indicate that the code to execute cannot be completed."""


class RequestException(PrawcoreException):
    """Indicate that there was an error with the HTTP request."""

    def __init__(self, response):
        """Initialize a RequestException instance..

        :param response: A requests.response instance.

        """
        self.response = response
        super(RequestException, self).__init__('error processing request ({})'
                                               .format(response.status_code))


class OAuthException(PrawcoreException):
    """Indicate that there was an OAuth2 related error with the request."""

    def __init__(self, response, error, description):
        """Intialize a OAuthException instance.

        :param response: A requests.response instance.
        :param error: The error type returned by reddit.
        :param description: A description of the error when provided.

        """
        self.error = error
        self.description = description
        self.response = response
        PrawcoreException.__init__(self, '{} error processing request ({})'
                                   .format(error, description))


class Forbidden(RequestException):
    """Indicate the authentication is not permitted for the request."""


class InsufficientScope(RequestException):
    """Indicate that the request requires a different scope."""


class InvalidToken(RequestException):
    """Indicate that the request used an invalid access token."""


class Redirect(RequestException):
    """Indicate the request resulted in a redirect.

    This class adds the attribute ``path``, which is the path to which the
    response redirects.

    """

    def __init__(self, response):
        """Initialize a Redirect exception instance..

        :param response: A requests.response instance containing a location
        header.

        """
        path = urlparse(response.headers['location']).path
        self.path = path[:-5] if path.endswith('.json') else path
        self.response = response
        PrawcoreException.__init__(self, 'Redirect to {}'.format(self.path))
