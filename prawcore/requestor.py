"""Provides the HTTP request handling interface."""
import requests
from .const import __version__
from .exceptions import InvalidInvocation


class Requestor(object):
    """Requestor provides an interface to HTTP requests."""

    def __init__(self, user_agent, oauth_url='https://oauth.reddit.com',
                 reddit_url='https://www.reddit.com'):
        """Create an instance of the Requestor class.

        :param user_agent: The user-agent for your application. Please follow
            reddit's user-agent guidlines:
            https://github.com/reddit/reddit/wiki/API#rules
        :param oauth_url: (Optional) The URL used to make OAuth requests to the
            reddit site. (Default: https://oauth.reddit.com)
        :param reddit_url: (Optional) The URL used when obtaining access
            tokens. (Default: https://www.reddit.com)

        """
        if user_agent is None or len(user_agent) < 7:
            raise InvalidInvocation('user_agent is not descriptive')

        self._http = requests.Session()
        self._http.headers['User-Agent'] = '{} prawcore/{}'.format(
            user_agent, __version__)

        self.oauth_url = oauth_url
        self.reddit_url = reddit_url

    def __getattr__(self, attribute):
        """Pass all undefined attributes to the _http attribute."""
        if attribute.startswith('__'):
            raise AttributeError
        return getattr(self._http, attribute)
