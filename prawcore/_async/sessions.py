"""prawcore.sessions: Provides prawcore.Session and prawcore.session."""

from __future__ import annotations

import asyncio
import logging
import random
import time
from abc import ABC, abstractmethod
from copy import deepcopy
from pprint import pformat
from typing import TYPE_CHECKING, Any, BinaryIO, TextIO
from urllib.parse import urljoin

from niquests.exceptions import ChunkedEncodingError, ConnectionError, ReadTimeout
from niquests.status_codes import codes

from .auth import AsyncBaseAuthorizer
from ..const import TIMEOUT, WINDOW_SIZE
from ..exceptions import (
    BadJSON,
    BadRequest,
    Conflict,
    InvalidInvocation,
    NotFound,
    Redirect,
    RequestException,
    ServerError,
    SpecialError,
    TooLarge,
    TooManyRequests,
    UnavailableForLegalReasons,
    URITooLong,
)
from .rate_limit import AsyncRateLimiter
from ..util import authorization_error_class

if TYPE_CHECKING:
    from niquests.models import Response

    from .auth import AsyncAuthorizer
    from .requestor import AsyncRequestor

log = logging.getLogger(__package__)


class AsyncRetryStrategy(ABC):
    """An abstract class for scheduling request retries.

    The strategy controls both the number and frequency of retry attempts.

    Instances of this class are immutable.

    """

    @abstractmethod
    def _sleep_seconds(self) -> float | None:
        pass

    async def sleep(self):
        """Sleep until we are ready to attempt the request."""
        sleep_seconds = self._sleep_seconds()
        if sleep_seconds is not None:
            message = f"Sleeping: {sleep_seconds:0.2f} seconds prior to retry"
            log.debug(message)
            await asyncio.sleep(sleep_seconds)


class AsyncSession:
    """The low-level connection interface to Reddit's API."""

    RETRY_EXCEPTIONS = (ChunkedEncodingError, ConnectionError, ReadTimeout)
    RETRY_STATUSES = {
        520,
        522,
        codes["bad_gateway"],
        codes["gateway_timeout"],
        codes["internal_server_error"],
        codes["request_timeout"],
        codes["service_unavailable"],
    }
    STATUS_EXCEPTIONS = {
        codes["bad_gateway"]: ServerError,
        codes["bad_request"]: BadRequest,
        codes["conflict"]: Conflict,
        codes["found"]: Redirect,
        codes["forbidden"]: authorization_error_class,
        codes["gateway_timeout"]: ServerError,
        codes["internal_server_error"]: ServerError,
        codes["media_type"]: SpecialError,
        codes["moved_permanently"]: Redirect,
        codes["not_found"]: NotFound,
        codes["request_entity_too_large"]: TooLarge,
        codes["request_uri_too_large"]: URITooLong,
        codes["service_unavailable"]: ServerError,
        codes["too_many_requests"]: TooManyRequests,
        codes["unauthorized"]: authorization_error_class,
        codes[
            "unavailable_for_legal_reasons"
        ]: UnavailableForLegalReasons,  # Cloudflare's status (not named in niquests)
        520: ServerError,
        522: ServerError,
    }
    SUCCESS_STATUSES = {codes["accepted"], codes["created"], codes["ok"]}

    @staticmethod
    def _log_request(
        data: list[tuple[str, str]] | None,
        method: str,
        params: dict[str, int],
        url: str,
    ):
        log.debug("Fetching: %s %s at %s", method, url, time.time())
        log.debug("Data: %s", pformat(data))
        log.debug("Params: %s", pformat(params))

    @property
    def _requestor(self) -> AsyncRequestor:
        return self._authorizer._authenticator._requestor

    async def __aenter__(self) -> AsyncSession:  # noqa: PYI034
        """Allow this object to be used as a context manager."""
        return self

    async def __aexit__(self, *_args):
        """Allow this object to be used as a context manager."""
        await self.close()

    def __init__(
        self,
        authorizer: AsyncBaseAuthorizer | None,
        window_size: int = WINDOW_SIZE,
    ):
        """Prepare the connection to Reddit's API.

        :param authorizer: An instance of :class:`.AsyncAuthorizer`.
        :param window_size: The size of the rate limit reset window in seconds.

        """
        if not isinstance(authorizer, AsyncBaseAuthorizer):
            msg = f"invalid Authorizer: {authorizer}"
            raise InvalidInvocation(msg)
        self._authorizer = authorizer
        self._rate_limiter = AsyncRateLimiter(window_size=window_size)
        self._retry_strategy_class = AsyncFiniteRetryStrategy

    async def _do_retry(
        self,
        data: list[tuple[str, Any]],
        files: dict[str, BinaryIO | TextIO],
        json: dict[str, Any],
        method: str,
        params: dict[str, int],
        response: Response | None,
        retry_strategy_state: AsyncFiniteRetryStrategy,
        saved_exception: Exception | None,
        timeout: float,
        url: str,
    ) -> dict[str, Any] | str | None:
        status = repr(saved_exception) if saved_exception else response.status_code
        log.warning("Retrying due to %s status: %s %s", status, method, url)
        return await self._request_with_retries(
            data=data,
            files=files,
            json=json,
            method=method,
            params=params,
            timeout=timeout,
            url=url,
            retry_strategy_state=retry_strategy_state.consume_available_retry(),
            # noqa: E501
        )

    async def _make_request(
        self,
        data: list[tuple[str, Any]],
        files: dict[str, BinaryIO | TextIO],
        json: dict[str, Any],
        method: str,
        params: dict[str, Any],
        retry_strategy_state: AsyncFiniteRetryStrategy,
        timeout: float,
        url: str,
    ) -> tuple[Response, None] | tuple[None, Exception]:
        try:
            response = await self._rate_limiter.call(
                self._requestor.request,
                self._set_header_callback,
                method,
                url,
                allow_redirects=False,
                data=data,
                files=files,
                json=json,
                params=params,
                timeout=timeout,
            )
            log.debug(
                "Response: %s (%s bytes) (rst-%s:rem-%s:used-%s ratelimit) at %s",
                response.status_code,
                response.headers.get("content-length"),
                response.headers.get("x-ratelimit-reset"),
                response.headers.get("x-ratelimit-remaining"),
                response.headers.get("x-ratelimit-used"),
                time.time(),
            )
            return response, None
        except RequestException as exception:
            if (
                not retry_strategy_state.should_retry_on_failure()
                or not isinstance(  # noqa: E501
                    exception.original_exception, self.RETRY_EXCEPTIONS
                )
            ):
                raise
            return None, exception.original_exception

    async def _request_with_retries(
        self,
        data: list[tuple[str, Any]],
        files: dict[str, BinaryIO | TextIO],
        json: dict[str, Any],
        method: str,
        params: dict[str, Any],
        timeout: float,
        url: str,
        retry_strategy_state: AsyncFiniteRetryStrategy | None = None,
    ) -> dict[str, Any] | str | None:
        if retry_strategy_state is None:
            retry_strategy_state = self._retry_strategy_class()

        await retry_strategy_state.sleep()
        self._log_request(data, method, params, url)
        response, saved_exception = await self._make_request(
            data,
            files,
            json,
            method,
            params,
            retry_strategy_state,
            timeout,
            url,
        )

        do_retry = False
        if response is not None and response.status_code == codes["unauthorized"]:
            self._authorizer._clear_access_token()
            if hasattr(self._authorizer, "refresh"):
                do_retry = True

        if retry_strategy_state.should_retry_on_failure() and (
            do_retry or response is None or response.status_code in self.RETRY_STATUSES
        ):
            return await self._do_retry(
                data,
                files,
                json,
                method,
                params,
                response,
                retry_strategy_state,
                saved_exception,
                timeout,
                url,
            )
        if response.status_code in self.STATUS_EXCEPTIONS:
            raise self.STATUS_EXCEPTIONS[response.status_code](response)
        if response.status_code == codes["no_content"]:
            return None
        assert (
            response.status_code in self.SUCCESS_STATUSES
        ), f"Unexpected status code: {response.status_code}"
        if response.headers.get("content-length") == "0":
            return ""
        try:
            return response.json()
        except ValueError:
            raise BadJSON(response) from None

    def _set_header_callback(self) -> dict[str, str]:
        if not self._authorizer.is_valid() and hasattr(self._authorizer, "refresh"):
            self._authorizer.refresh()
        return {"Authorization": f"bearer {self._authorizer.access_token}"}

    async def close(self):
        """Close the session and perform any clean up."""
        await self._requestor.close()

    async def request(
        self,
        method: str,
        path: str,
        data: dict[str, Any] | None = None,
        files: dict[str, BinaryIO | TextIO] | None = None,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        timeout: float = TIMEOUT,
    ) -> dict[str, Any] | str | None:
        """Return the json content from the resource at ``path``.

        :param method: The request verb. E.g., ``"GET"``, ``"POST"``, ``"PUT"``.
        :param path: The path of the request. This path will be combined with the
            ``oauth_url`` of the Requestor.
        :param data: Dictionary, bytes, or file-like object to send in the body of the
            request.
        :param files: Dictionary, mapping ``filename`` to file-like object.
        :param json: Object to be serialized to JSON in the body of the request.
        :param params: The query parameters to send with the request.
        :param timeout: Specifies a particular timeout, in seconds.

        Automatically refreshes the access token if it becomes invalid and a refresh
        token is available.

        :raises: :class:`.InvalidInvocation` in such a case if a refresh token is not
            available.

        """
        params = deepcopy(params) or {}
        params["raw_json"] = 1
        if isinstance(data, dict):
            data = deepcopy(data)
            data["api_type"] = "json"
            data = sorted(data.items())
        if isinstance(json, dict):
            json = deepcopy(json)
            json["api_type"] = "json"
        url = urljoin(self._requestor.oauth_url, path)
        return await self._request_with_retries(
            data=data,
            files=files,
            json=json,
            method=method,
            params=params,
            timeout=timeout,
            url=url,
        )


def async_session(
    authorizer: AsyncAuthorizer | None = None,
    window_size: int = WINDOW_SIZE,
) -> AsyncSession:
    """Return a :class:`.AsyncSession` instance.

    :param authorizer: An instance of :class:`.AsyncAuthorizer`.
    :param window_size: The size of the rate limit reset window in seconds.

    """
    return AsyncSession(authorizer=authorizer, window_size=window_size)


class AsyncFiniteRetryStrategy(AsyncRetryStrategy):
    """A ``RetryStrategy`` that retries requests a finite number of times."""

    def __init__(self, retries: int = 3):
        """Initialize the strategy.

        :param retries: Number of times to attempt a request (default: ``3``).

        """
        self._retries = retries

    def _sleep_seconds(self) -> float | None:
        if self._retries < 3:
            base = 0 if self._retries == 2 else 2
            return base + 2 * random.random()  # noqa: S311
        return None

    def consume_available_retry(self) -> AsyncFiniteRetryStrategy:
        """Allow one fewer retry."""
        return type(self)(self._retries - 1)

    def should_retry_on_failure(self) -> bool:
        """Return ``True`` if and only if the strategy will allow another retry."""
        return self._retries > 1
