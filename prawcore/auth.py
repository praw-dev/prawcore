"""Provides Authentication and Authorization classes."""
import time
from . import const
from .exceptions import InvalidInvocation, OAuthException, ResponseException
from requests import Request
from requests.status_codes import codes


class Authenticator(object):
    """Stores OAuth2 authentication credentials."""

    def __init__(self, requestor, client_id, client_secret=None,
                 redirect_uri=None):
        """Represent a single authentication to reddit's API.

        :param requestor: An instance of :class:`Requestor`.
        :param client_id: The OAuth2 client ID to use with the session.
        :param client_secret: (optional) The OAuth2 client secret to use with
            the session. This parameter is required for use with all
            Authorizers save for DeviceIDAuthorizer.
        :param redirect_uri: (optional) The redirect URI exactly as specified
            in your OAuth application settings on reddit. This parameter is
            required if you want to use the ``authorize_url`` method, or the
            ``authorize`` method of the ``Authorizer`` class.

        """
        self._requestor = requestor
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def _post(self, url, success_status=codes['ok'], **data):
        auth = (self.client_id, self.client_secret or '')
        response = self._requestor.request('post', url, auth=auth,
                                           data=sorted(data.items()))
        if response.status_code != success_status:
            raise ResponseException(response)
        return response

    def authorize_url(self, duration, scopes, state):
        """Return the URL used out-of-band to grant access to your application.

        :param duration: Either ``permanent`` or ``temporary``. ``temporary``
            authorizations generate access tokens that last only 1
            hour. ``permanent`` authorizations additionally generate a refresh
            token that can be indefinitely used to generate new hour-long
            access tokens.
        :param scopes: A list of OAuth scopes to request authorization for.
        :param state: A string that will be reflected in the callback to
            ``redirect_uri``. This value should be temporarily unique to the
            client for whom the URL was generated for.

        """
        if self.redirect_uri is None:
            raise InvalidInvocation('redirect URI not provided')

        params = {'client_id': self.client_id, 'duration': duration,
                  'redirect_uri': self.redirect_uri, 'response_type': 'code',
                  'scope': ' '.join(scopes), 'state': state}
        url = self._requestor.reddit_url + const.AUTHORIZATION_PATH
        request = Request('GET', url, params=params)
        return request.prepare().url

    def revoke_token(self, token, token_type=None):
        """Ask reddit to revoke the provided token.

        :param token: The access or refresh token to revoke.
        :param token_type: (Optional) When provided, hint to reddit what the
            token type is for a possible efficiency gain. The value can be
            either ``access_token`` or ``refresh_token``.

        """
        data = {'token': token}
        if token_type is not None:
            data['token_type_hint'] = token_type
        url = self._requestor.reddit_url + const.REVOKE_TOKEN_PATH
        self._post(url, success_status=codes['no_content'], **data)


class Authorizer(object):
    """Manages OAuth2 authorization tokens and scopes."""

    def __init__(self, authenticator, refresh_token=None):
        """Represent a single authorization to reddit's API.

        :param authenticator: An instance of :class:`Authenticator`.
        :param refresh_token: (Optional) Enables the ability to refresh the
            authorization.

        """
        self._authenticator = authenticator
        self.refresh_token = refresh_token
        self._clear_access_token()
        self._validate_authenticator()

    def _clear_access_token(self):
        self._expiration_timestamp = None
        self.access_token = None
        self.scopes = None

    def _request_token(self, **data):
        url = (self._authenticator._requestor.reddit_url +
               const.ACCESS_TOKEN_PATH)
        pre_request_time = time.time()
        response = self._authenticator._post(url, **data)
        payload = response.json()
        if 'error' in payload:  # Why are these OKAY responses?
            raise OAuthException(response, payload['error'],
                                 payload.get('error_description'))

        self._expiration_timestamp = (pre_request_time - 10
                                      + payload['expires_in'])
        self.access_token = payload['access_token']
        if 'refresh_token' in payload:
            self.refresh_token = payload['refresh_token']
        self.scopes = set(payload['scope'].split(' '))

    def _validate_authenticator(self):
        if not self._authenticator.client_secret:
            raise InvalidInvocation('Authorizer must be used with an '
                                    'Authenticator that has a client secret.')

    def authorize(self, code):
        """Obtain and set authorization tokens based on ``code``.

        :param code: The code obtained by an out-of-band authorization request
            to reddit.

        """
        if self._authenticator.redirect_uri is None:
            raise InvalidInvocation('redirect URI not provided')
        self._request_token(code=code, grant_type='authorization_code',
                            redirect_uri=self._authenticator.redirect_uri)

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

    def revoke(self, only_access=False):
        """Revoke the current Authorization.

        :param only_access: (Optional) When explicitly set to True, do not
            evict the refresh token if one is set.

        Revoking a refresh token will in-turn revoke all access tokens
        associated with that authorization.

        """
        if self.refresh_token is not None and not only_access:
            self._authenticator.revoke_token(self.refresh_token,
                                             'refresh_token')
        elif self.access_token is not None:
            self._authenticator.revoke_token(self.access_token, 'access_token')
        else:
            raise InvalidInvocation('no token available to revoke')

        self._clear_access_token()
        if not only_access:
            self.refresh_token = None


class DeviceIDAuthorizer(Authorizer):
    """Manages app-only OAuth2 for 'installed' applications.

    While the '*' scope will be available, some endpoints simply will not work
    due to the lack of an associated reddit account.
    """

    def __init__(self, authenticator, device_id='DO_NOT_TRACK_THIS_DEVICE'):
        """Represent an app-only OAuth2 authorization for 'installed' apps.

        :param authenticator: An instance of :class:`Authenticator`.
        :param device_id: (optional) A unique ID (20-30 character ASCII string)
            (default DO_NOT_TRACK_THIS_DEVICE). For more information about this
            parameter, see:
            https://github.com/reddit/reddit/wiki/OAuth2#application-only-oauth
        """
        super(DeviceIDAuthorizer, self).__init__(authenticator)
        self._device_id = device_id

    def _validate_authenticator(self):
        if self._authenticator.client_secret:
            raise InvalidInvocation('DeviceIDAuthorizor cannot be used with an'
                                    ' Authenticator that has a client secret.')

    def refresh(self):
        """Obtain a new access token."""
        grant_type = 'https://oauth.reddit.com/grants/installed_client'
        self._request_token(grant_type=grant_type,
                            device_id=self._device_id)


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
