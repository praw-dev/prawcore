"""Provide utility for the prawcore package."""
from .exceptions import InsufficientScope, InvalidToken


_auth_error_mapping = {'insufficient_scope': InsufficientScope,
                       'invalid_token': InvalidToken}


def authorization_error_class(response):
    """Return an exception instance that maps to the OAuth Error.

    :param response: The HTTP response containing a www-authenticate error.

    """
    message = response.headers['www-authenticate']
    error = message.replace('"', '').rsplit('=', 1)[1]
    return _auth_error_mapping[error](response)
