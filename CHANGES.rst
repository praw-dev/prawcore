Change Log
==========

prawcore follows `semantic versioning <http://semver.org/>`_.

Unreleased
----------

**Added**

- 301 redirects result in a ``Redirect`` exception.
- ``Requestor`` is now initialzed with a ``timeout`` parameter.
- ``ScriptAuthorizer``, ``ReadOnlyAuthorizer``, and ``DeviceIDAuthorizer`` have a
  new parameter, ``scopes``, which determines the scope of access requests.

2.2.0 (2021-06-10)
------------------

**Added**

- Support 202 "Accepted" HTTP responses.

**Fixed**

- The expected HTTP response status code for a request made with the proper credentials
  to api/v1/revoke_token has been changed from 204 to 200.

2.1.0 (2021-06-07)
------------------

**Added**

- Add a ``URITooLarge`` exception.
- :class:`.ScriptAuthorizer` has a new parameter ``two_factor_callback`` that supplies
  OTPs (One-Time Passcodes) when :meth:`.ScriptAuthorizer.refresh` is called.
- Add a ``TooManyRequests`` exception.

2.0.0 (2021-02-23)
------------------

**Added**

- ``Authorizer`` optionally takes a ``pre_refresh_callback`` keyword
  argument. If provided, the function will called with the instance of
  ``Authorizer`` prior to refreshing the access and refresh tokens.
- ``Authorizer`` optionally takes a ``post_refresh_callback`` keyword
  argument. If provided, the function will called with the instance of
  ``Authorizer`` after refreshing the access and refresh tokens.

**Changed**

- The ``refresh_token`` argument to ``Authorizer`` must now be passed by
  keyword, and cannot be passed as a positional argument.

1.5.0 (2020-08-04)
------------------

**Changed**

- Drop support for Python 3.5, which is end-of-life on 2020-09-13.

1.4.0 (2020-05-28)
------------------

**Added**

- When calling :meth:`.Session.request`, we add the key-value pair ``"api_type":
  "json"`` to the ``json`` parameter, if it is a ``dict``.

**Changed**

- (Non-breaking) Requests to ``www.reddit.com`` use the ``Connection: close`` header to
  avoid warnings when tokens are refreshed after their one-hour expiration.

1.3.0 (2020-04-23)
------------------

**Added**

- All other requestor methods, most notably :meth:`.Session.request`, now contain a
  ``timeout`` parameter.

1.2.0 (2020-04-23)
------------------

**Added**

- Method ``Requestor.request`` can be given a timeout parameter to control the amount of
  time to wait for a request to succeed.

**Changed**

- Updated rate limit algorithm to more intelligently rate limit when there are extra
  requests remaining.

**Removed**

- Drop python 2.7 support.

1.0.1 (2019-02-05)
------------------

**Fixed**

- ``RateLimiter`` will not sleep longer than ``next_request_timestamp``.

1.0.0 (2018-04-26)
------------------

I am releasing 1.0.0 as prawcore is quite stable and it's unlikely that any breaking
changes will need to be introduced in the near future.

**Added**

- Log debug messages for all sleep times.

0.15.0 (2018-03-31)
-------------------

**Added**

- ``SpecialError`` is raised on HTTP 415.

0.14.0 (2018-02-10)
-------------------

**Added**

- ``ReadTimeout`` is automatically retried like the server errors.

**Removed**

- Removed support for Python 3.3 as it is no longer supported by requests.

0.13.0 (2017-12-16)
-------------------

**Added**

- ``UnavailableForLegalReasons`` exception raised when HTTP Response 451 is encountered.

0.12.0 (2017-08-30)
-------------------

**Added**

- ``BadJSON`` exception for the rare cases that a response that should contain valid
  JSON has unparsable JSON.

0.11.0 (2017-05-27)
-------------------

**Added**

- ``Conflict`` exception is raised when response status 409 is returned.

0.10.1 (2017-04-10)
-------------------

**Fixed**

- ``InvalidToken`` is again raised on 401 when a non-refreshable application is in use.

0.10.0 (2017-04-10)
-------------------

**Added**

- ``ConnectionError`` exceptions are automatically retried. This handles ``Connection
  Reset by Peer`` issues that appear to occur somewhat frequently when running on Amazon
  EC2.

**Changed**

- Calling ``RateLimiter`` now requires a second positional argument,
  ``set_header_callback``.
- In the event a 401 unauthorized occurs, the access token is cleared and the request is
  retried.

**Fixed**

- Check if the access token is expired immediately before every authorized request,
  rather than just before the request flow. This new approach accounts for failure
  retries, and rate limiter delay.

0.9.0 (2017-03-11)
------------------

**Added**

- Add ``session`` parameter to Requestor to ease support of custom sessions (e.g.
  caching or mock ones).

0.8.0 (2017-01-29)
------------------

**Added**

- Handle 413 Request entity too large responses.
- ``reset_timestamp`` to ``RateLimiter``.

**Fixed**

- Avoid modifying passed in ``data`` and ``params`` to ``Session.request``.

0.7.0 (2017-01-16)
------------------

**Added**

``ChunkedEncodingError`` is automatically retried like the server errors.

0.6.0 (2016-12-24)
------------------

**Added**

- Handle 500 responses.
- Handle Cloudflare 520 responses.

0.5.0 (2016-12-13)
------------------

**Added**

All network requests now have a 16 second timeout by default. The environment variable
``prawcore_timeout`` can be used to adjust the value.

0.4.0 (2016-12-09)
------------------

**Changed**

- Prevent '(None)' from appearing in OAuthException message.

0.3.0 (2016-11-20)
------------------

**Added**

- Add ``files`` parameter to ``Session.request`` to support image upload operations.
- Add ``duration`` and ``implicit`` parameters to
  ``UntrustedAuthenticator.authorization_url`` so that the method also supports the code
  grant flow.

**Fixed**

- ``Authorizer`` class can be used with ``UntrustedAuthenticator``.

0.2.1 (2016-08-07)
------------------

**Fixed**

- ``session`` works with ``DeviceIDAuthorizer`` and ``ImplicitAuthorizer``.

0.2.0 (2016-08-07)
------------------

**Added**

- Add ``ImplicitAuthorizer``.

**Changed**

- Split ``Authenticator`` into ``TrustedAuthenticator`` and ``UntrustedAuthenticator``.

0.1.1 (2016-08-06)
------------------

**Added**

- Add ``DeviceIDAuthorizer`` that permits installed application access to the API.

0.1.0 (2016-08-05)
------------------

**Added**

- ``RequestException`` which wraps all exceptions that occur from ``requests.request``
  in a ``prawcore.RequestException``.

**Changed**

- What was previously ``RequestException`` is now ``ResponseException``.

0.0.15 (2016-08-02)
-------------------

**Added**

- Handle Cloudflare 522 responses.

0.0.14 (2016-07-25)
-------------------

**Added**

- Add ``ServerError`` exception for 502, 503, and 504 HTTP status codes that is only
  raised after three failed attempts to make the request.
- Add ``json`` parameter to ``Session.request``.

0.0.13 (2016-07-24)
-------------------

**Added**

- Automatically attempt to refresh access tokens when making a request if the access
  token is expired.

**Fixed**

- Consider access tokens expired slightly earlier than allowed for to prevent
  InvalidToken exceptions from occuring.

0.0.12 (2016-07-17)
-------------------

**Added**

- Handle 0-byte HTTP 200 responses.

0.0.11 (2016-07-16)
-------------------

**Added**

- Add a ``NotFound`` exception.
- Support 404 "Not Found" HTTP responses.

0.0.10 (2016-07-10)
-------------------

**Added**

- Add a ``BadRequest`` exception.
- Support 400 "Bad Request" HTTP responses.
- Support 204 "No Content" HTTP responses.

0.0.9 (2016-07-09)
------------------

**Added**

- Support 201 "Created" HTTP responses used in some v1 endpoints.

0.0.8 (2016-03-21)
------------------

**Added**

- Sort ``Session.request`` ``data`` values. Sorting the values permits betamax body
  matcher to work as expected.

0.0.7 (2016-03-18)
------------------

**Added**

- Added ``data`` parameter to ``Session.request``.

0.0.6 (2016-03-14)
------------------

**Fixed**

- prawcore objects can be pickled.

0.0.5 (2016-03-12)
------------------

**Added**

- 302 redirects result in a ``Redirect`` exception.

0.0.4 (2016-03-12)
------------------

**Added**

- Add a generic ``Forbidden`` exception for 403 responses without the
  ``www-authenticate`` header.

0.0.3 (2016-02-29)
------------------

**Added**

- Added ``params`` parameter to ``Session.request``.
- Log requests to the ``prawcore`` logger in debug mode.

0.0.2 (2016-02-21)
------------------

**Fixed**

- README.rst for display purposes on pypi.

0.0.1 (2016-02-17) [YANKED]
---------------------------

**Added**

- Dynamic rate limiting based on reddit's response headers.
- Authorization URL generation.
- Retrieval of access and refresh tokens from authorization grants.
- Access and refresh token revocation.
- Retrieval of read-only access tokens.
- Retrieval of script-app tokens.
- Three examples in the ``examples/`` directory.
