"""Provides Authentication and Authorization classes."""
import time
from . import const, util
from .exceptions import InvalidInvocation, OAuthException, RequestException
from requests.status_codes import codes


class Authenticator(object):
    """Stores OAuth2 authentication credentials."""

    def __init__(self, client_id, client_secret):
        """Represent a single authentication to reddit's API.

        :param client_id: The OAuth2 client id to use with the session.
        :param client_secret: The OAuth2 client secret to use with the session.

        """
        self.client_id = client_id
        self.client_secret = client_secret


class Authorizer(object):
    """Manages OAuth2 authorization tokens and scopes."""

    def __init__(self, authenticator, refresh_token=None):
        """Represent a single authorization to reddit's API.

        :param authenticator: An instance of :class:`Authenticator`.
        :param refresh_token: (Optional) Enables the ability to refresh the
            authorization.

        """
        self._auth = (authenticator.client_id, authenticator.client_secret)
        self._expiration_timestamp = None
        self._session = util.http

        self.access_token = None
        self.refresh_token = refresh_token
        self.scopes = None

    def _request_token(self, **data):
        response = self._session.post(const.ACCESS_TOKEN_URL, auth=self._auth,
                                      data=data)
        if response.status_code != codes['ok']:
            raise RequestException(response)

        payload = response.json()

        if 'error' in payload:  # Why are these OKAY responses?
            raise OAuthException(response, payload['error'],
                                 payload.get('error_description'))

        self._expiration_timestamp = time.time() + payload['expires_in']
        self.access_token = payload['access_token']
        self.scopes = set(payload['scope'].split(' '))

    def is_valid(self):
        """Return whether or not the Authorizer is ready to authorize requests.

        A ``True`` return value does not guarantee that the access_token is
        actually valid on the server side.

        """
        return self.access_token is not None \
            and time.time() < self._expiration_timestamp

    def refresh(self):
        """Obtain a new access token from the refresh_token."""
        if self.refresh_token is None:
            raise InvalidInvocation('refresh token not provided')
        self._request_token(grant_type='refresh_token',
                            refresh_token=self.refresh_token)


class ReadOnlyAuthorizer(Authorizer):
    """Manages authorizations that are not associated with a reddit account.

    While the '*' scope will be available, some endpoints simply will not work
    due to the lack of an associated reddit account.

    """

    def refresh(self):
        """Obtain a new ReadOnly access token."""
        self._request_token(grant_type='client_credentials')


class ScriptAuthorizer(Authorizer):
    """Manages personal-use script type authorizations.

    Only users who are listed as developers for the application will be
    granted access tokens.

    """

    def __init__(self, authenticator, username, password):
        """Represent a single personal-use authorization to reddit's API.

        :param authenticator: An instance of :class:`Authenticator`.
        :param username: The reddit username of one of the application's
            developers.
        :param password: The password associated with ``username``.

        """
        super(ScriptAuthorizer, self).__init__(authenticator)
        self._username = username
        self._password = password

    def refresh(self):
        """Obtain a new personal-use script type access token."""
        self._request_token(grant_type='password', username=self._username,
                            password=self._password)
