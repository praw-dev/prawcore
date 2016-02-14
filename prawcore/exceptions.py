"""Provide exception classes for the prawcore package."""


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


class InsufficientScope(RequestException):
    """Indicate that the request requires a different scope."""


class InvalidToken(RequestException):
    """Indicate that the request used an invalid access token."""
