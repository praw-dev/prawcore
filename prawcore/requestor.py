"""Provides the HTTP request handling interface."""
import requests
from . import const


class Requestor(object):
    """Requestor provides an interface to HTTP requests."""

    def __init__(self, user_agent):
        """Create an instance of the Requestor class.

        :param user_agent: The user-agent for your application. Please follow
            reddit's user-agent guidlines:
            ttps://github.com/reddit/reddit/wiki/API#rules

        """
        self._http = requests.Session()
        self._http.headers['User-Agent'] = '{} {}'.format(
            user_agent, const.USER_AGENT)

    def __getattr__(self, attribute):
        """Pass all undefined attributes to the _http attribute."""
        return getattr(self._http, attribute)
