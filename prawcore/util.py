"""Provide utility for the prawcore package."""
import requests
from . import const
from .exceptions import InsufficientScope, InvalidToken

http = requests.Session()
http.headers['User-Agent'] = const.USER_AGENT


_auth_error_mapping = {'insufficient_scope': InsufficientScope,
                       'invalid_token': InvalidToken}


def authorization_error_class(response):
    """Return an exception instance that maps to the OAuth Error.

    :param response: The HTTP response containing a www-authenticate error.

    """
    message = response.headers['www-authenticate']
    error = message.replace('"', '').rsplit('=', 1)[1]
    return _auth_error_mapping[error](response)
