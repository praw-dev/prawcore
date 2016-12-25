"""prawcore.sessions: Provides prawcore.Session and prawcore.session."""
import logging
import random
import time

from requests.compat import urljoin
from requests.status_codes import codes

from .auth import BaseAuthorizer
from .rate_limit import RateLimiter
from .exceptions import (BadRequest, InvalidInvocation, NotFound, Redirect,
                         ServerError)
from .util import authorization_error_class

log = logging.getLogger(__package__)


class Session(object):
    """The low-level connection interface to reddit's API."""

    RETRY_STATUSES = {520, 522, codes['bad_gateway'], codes['gateway_timeout'],
                      codes['internal_server_error'],
                      codes['service_unavailable']}
    STATUS_EXCEPTIONS = {codes['bad_gateway']: ServerError,
                         codes['bad_request']: BadRequest,
                         codes['found']: Redirect,
                         codes['forbidden']: authorization_error_class,
                         codes['gateway_timeout']: ServerError,
                         codes['internal_server_error']: ServerError,
                         codes['not_found']: NotFound,
                         codes['service_unavailable']: ServerError,
                         codes['unauthorized']: authorization_error_class,
                         # CloudFlare status (not named in requests)
                         520: ServerError,
                         522: ServerError}
    SUCCESS_STATUSES = {codes['created'], codes['ok']}

    def __init__(self, authorizer):
        """Preprare the connection to reddit's API.

        :param authorizer: An instance of :class:`Authorizer`.

        """
        if not isinstance(authorizer, BaseAuthorizer):
            raise InvalidInvocation('invalid Authorizer: {}'
                                    .format(authorizer))
        self._authorizer = authorizer
        self._rate_limiter = RateLimiter()

    def __enter__(self):
        """Allow this object to be used as a context manager."""
        return self

    def __exit__(self, *_args):
        """Allow this object to be used as a context manager."""
        self.close()

    def _request_with_retries(self, data, files, headers, json, method,
                              params, url, retries=3):
        if retries < 3:
            base = 0 if retries == 2 else 2
            sleep_time = base + 2 * random.random()
            log.debug('Sleeping: {:0.2f} seconds'.format(sleep_time))
            time.sleep(sleep_time)
        log.debug('Fetching: {} {}'.format(method, url))
        log.debug('Headers: {}'.format(headers))
        log.debug('Data: {}'.format(data))
        log.debug('Params: {}'.format(params))
        response = self._rate_limiter.call(self._requestor.request,
                                           method, url, allow_redirects=False,
                                           data=data, files=files,
                                           headers=headers, json=json,
                                           params=params)

        log.debug('Response: {} ({} bytes)'.format(
            response.status_code, response.headers.get('content-length')))

        if response.status_code in self.RETRY_STATUSES and retries > 1:
            log.warning('Retrying due to {} status: {} {}'
                        .format(response.status_code, method, url))
            return self._request_with_retries(
                data=data, files=files, headers=headers, json=json,
                method=method, params=params, url=url, retries=retries - 1)
        elif response.status_code in self.STATUS_EXCEPTIONS:
            raise self.STATUS_EXCEPTIONS[response.status_code](response)
        elif response.status_code == codes['no_content']:
            return
        assert response.status_code in self.SUCCESS_STATUSES, \
            'Unexpected status code: {}'.format(response.status_code)
        if response.headers.get('content-length') == '0':
            return ''
        return response.json()

    @property
    def _requestor(self):
        return self._authorizer._authenticator._requestor

    def close(self):
        """Close the session and perform any clean up."""
        self._requestor.close()

    def request(self, method, path, data=None, files=None, json=None,
                params=None):
        """Return the json content from the resource at ``path``.

        :param method: The request verb. E.g., get, post, put.
        :param path: The path of the request. This path will be combined with
            the ``oauth_url`` of the Requestor.
        :param data: Dictionary, bytes, or file-like object to send in the body
            of the request.
        :param files: Dictionary, mapping ``filename`` to file-like object.
        :param json: Object to be serialized to JSON in the body of the
            request.
        :param params: The query parameters to send with the request.

        Automatically refreshes the access token if it becomes invalid and a
        refresh token is available. Raises InvalidInvocation in such a case if
        a refresh token is not available.

        """
        if not self._authorizer.is_valid():
            self._authorizer.refresh()

        headers = {'Authorization': 'bearer {}'
                   .format(self._authorizer.access_token)}
        params = params or {}
        params['raw_json'] = 1
        if isinstance(data, dict):
            data['api_type'] = 'json'
            data = sorted(data.items())
        url = urljoin(self._requestor.oauth_url, path)
        return self._request_with_retries(
            data=data, files=files, headers=headers, json=json, method=method,
            params=params,  url=url)


def session(authorizer=None):
    """Return a :class:`Session` instance.

    :param authorizer: An instance of :class:`Authorizer`.

    """
    return Session(authorizer=authorizer)
