"""Provide exception classes for the prawcore package."""


class PrawcoreException(Exception):
    """Base exception class for exceptions that occur within this package."""


class InvalidInvocation(PrawcoreException):
    """Indicate that the code to execute cannot be completed."""


class RequestException(PrawcoreException):
    """Indicate that there was an error with the HTTP request."""

    def __init__(self, response):
        """RequestException instances contain the failing response.

        :param response: A requests.response instance.

        """
        self.response = response
        super(RequestException, self).__init__('error processing request ({})'
                                               .format(response.status_code))


class InsufficientScope(RequestException):
    """Indicate that the request requires a different scope."""


class InvalidToken(RequestException):
    """Indicate that the request used an invalid access token."""
