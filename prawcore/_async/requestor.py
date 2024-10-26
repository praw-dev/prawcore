"""Provides the HTTP request handling interface."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import niquests

from ..const import TIMEOUT
from ..exceptions import InvalidInvocation, RequestException

if TYPE_CHECKING:
    from niquests import AsyncSession, Response


class AsyncRequestor:
    """Requestor provides an interface to HTTP requests."""

    def __getattr__(self, attribute: str) -> Any:
        """Pass all undefined attributes to the ``_http`` attribute."""
        if attribute.startswith("__"):
            raise AttributeError
        return getattr(self._http, attribute)

    def __init__(
        self,
        user_agent: str,
        oauth_url: str = "https://oauth.reddit.com",
        reddit_url: str = "https://www.reddit.com",
        session: AsyncSession | None = None,
        timeout: float = TIMEOUT,
    ):
        """Create an instance of the Requestor class.

        :param user_agent: The user-agent for your application. Please follow Reddit's
            user-agent guidelines: https://github.com/reddit/reddit/wiki/API#rules
        :param oauth_url: The URL used to make OAuth requests to the Reddit site
            (default: ``"https://oauth.reddit.com"``).
        :param reddit_url: The URL used when obtaining access tokens (default:
            ``"https://www.reddit.com"``).
        :param session: A session instance to handle requests, compatible with
            ``niquests.Session()`` (default: ``None``).
        :param timeout: How many seconds to wait for the server to send data before
            giving up (default: ``prawcore.const.TIMEOUT``).

        """
        # Imported locally to avoid an import cycle, with __init__
        from .. import __version__

        if user_agent is None or len(user_agent) < 7:
            msg = "user_agent is not descriptive"
            raise InvalidInvocation(msg)

        self._http = session or niquests.AsyncSession()
        self._http.headers["User-Agent"] = f"{user_agent} prawcore/{__version__}"

        self.oauth_url = oauth_url
        self.reddit_url = reddit_url
        self.timeout = timeout

    async def close(self):
        """Call close on the underlying session."""
        await self._http.close()

    async def request(
        self, *args: Any, timeout: float | None = None, **kwargs: Any
    ) -> Response:
        """Issue the HTTP request capturing any errors that may occur."""
        try:
            return await self._http.request(
                *args, timeout=timeout or self.timeout, **kwargs
            )
        except Exception as exc:  # noqa: BLE001
            raise RequestException(exc, args, kwargs) from exc
