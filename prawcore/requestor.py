"""Provides the HTTP request handling interface."""
import requests
import aiohttp
import asyncio
from abc import ABC, abstractmethod
from .const import __version__, TIMEOUT
from .exceptions import InvalidInvocation, RequestException


class RequestorBase(ABC):
    def __init__(
        self,
        user_agent,
        oauth_url="https://oauth.reddit.com",
        reddit_url="https://www.reddit.com",
        session=None,
        loop=None
    ):
        """Create an instance of the Requestor class.

        :param user_agent: The user-agent for your application. Please follow
            reddit's user-agent guidelines:
            https://github.com/reddit/reddit/wiki/API#rules
        :param oauth_url: (Optional) The URL used to make OAuth requests to the
            reddit site. (Default: https://oauth.reddit.com)
        :param reddit_url: (Optional) The URL used when obtaining access
            tokens. (Default: https://www.reddit.com)
        :param session: (Optional) A session to handle requests, compatible
            with requests.Session(). (Default: None)
        :param loop: (Optional) The event loop for async tasks
        """
        if user_agent is None or len(user_agent) < 7:
            raise InvalidInvocation("user_agent is not descriptive")
        self.user_agent = user_agent
        self.original_session = session
        self.original_event_loop = loop
        self.oauth_url = oauth_url
        self.reddit_url = reddit_url
        self._http = self._init_session()

    def _get_headers(self):
        return {
            'User-Agent': "{} prawcore/{}".format(self.user_agent, __version__)
        }

    @abstractmethod
    def _init_session(self):
        pass

    @abstractmethod
    def request(self):
        pass

    def __getattr__(self, attribute):
        """Pass all undefined attributes to the _http attribute."""
        if attribute.startswith("__"):
            raise AttributeError
        return getattr(self._http, attribute)


class Requestor(RequestorBase):
    """Requestor provides an interface to HTTP requests."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _init_session(self):
        """Initializes the session with the headers"""
        headers = self._get_headers()
        session = self.original_session or requests.Session()
        session.headers.update(headers)
        return session

    def request(self, *args, timeout=TIMEOUT, **kwargs):
        """Issue the HTTP request capturing any errors that may occur."""
        try:
            return self._http.request(*args, timeout=timeout, **kwargs)
        except Exception as exc:
            raise RequestException(exc, args, kwargs)

    def close(self):
        """Call close on the underlying session."""
        return self._http.close()


class RequestorAsync(RequestorBase):
    """Requestor provides an interface to HTTP requests."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _init_session(self):
        loop = self.original_event_loop or asyncio.get_event_loop()
        session = self.original_session or aiohttp.ClientSession(
            loop=loop,
            headers=self._get_headers()
        )
        return session

    async def request(self, *args, timeout=TIMEOUT, **kwargs):
        """Issue the HTTP request capturing any errors that may occur."""
        try:
            return self._http.request(*args, timeout=timeout, **kwargs)
        except Exception as exc:
            raise RequestException(exc, args, kwargs)

    def close(self):
        """Call close on the underlying session."""
        return self.loop.run_until_complete(self._http.close())

