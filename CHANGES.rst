Change Log
==========

prawcore follows `semantic versioning <http://semver.org/>`_ with the exception
that deprecations will not be announced by a minor release.

0.6.0 (2016-12-24)
------------------

**Added**

* Handle 500 responses.
* Handle Cloudflair 520 responses.


0.5.0 (2016-12-13)
------------------

**Added**

All network requests now have a 16 second timeout by default. The environment
variable ``prawcore_timeout`` can be used to adjust the value.

0.4.0 (2016-12-09)
------------------

**Changed**

* Prevent '(None)' from appearing in OAuthException message.

0.3.0 (2016-11-20)
------------------

**Added**

* Add ``files`` parameter to ``Session.request`` to support image upload
  operations.
* Add ``duration`` and ``implicit`` parameters to
  ``UntrustedAuthenticator.authorization_url`` so that the method also supports
  the code grant flow.

**Fixed**

* ``Authorizer`` class can be used with ``UntrustedAuthenticator``.

0.2.1 (2016-08-07)
------------------

**Fixed**

* ``session`` works with ``DeviceIDAuthorizer`` and ``ImplicitAuthorizer``.


0.2.0 (2016-08-07)
------------------

**Added**

* Add ``ImplicitAuthorizer``.

**Changed**

* Split ``Authenticator`` into ``TrustedAuthenticator`` and
  ``UntrustedAuthenticator``.

0.1.1 (2016-08-06)
------------------

**Added**

* Add ``DeviceIDAuthorizer`` that permits installed application access to the
  API.

0.1.0 (2016-08-05)
------------------

**Added**

* ``RequestException`` which wraps all exceptions that occur from
  ``requests.request`` in a ``prawcore.RequestException``.

**Changed**

* What was previously ``RequestException`` is now ``ResponseException``.

0.0.15 (2016-08-02)
-------------------

**Added**

* Handle Cloudflair 522 responses.

0.0.14 (2016-07-25)
-------------------

**Added**

* Add ``ServerError`` exception for 502, 503, and 504 HTTP status codes that is
  only raised after three failed attempts to make the request.
* Add ``json`` parameter to ``Session.request``.

0.0.13 (2016-07-24)
-------------------

**Added**

* Automatically attempt to refresh access tokens when making a request if the
  access token is expired.

**Fixed**

* Consider access tokens expired slightly earlier than allowed for to prevent
  InvalidToken exceptions from occuring.

0.0.12 (2016-07-17)
-------------------

**Added**

* Handle 0-byte HTTP 200 responses.

0.0.11 (2016-07-16)
-------------------

**Added**

* Add a ``NotFound`` exception.
* Support 404 "Not Found" HTTP responses.


0.0.10 (2016-07-10)
-------------------

**Added**

* Add a ``BadRequest`` exception.
* Support 400 "Bad Request" HTTP responses.
* Support 204 "No Content" HTTP responses.

0.0.9 (2016-07-09)
------------------

**Added**

* Support 201 "Created" HTTP responses used in some v1 endpoints.


0.0.8 (2016-03-21)
------------------

**Added**

* Sort ``Session.request`` ``data`` values. Sorting the values permits betamax
  body matcher to work as expected.


0.0.7 (2016-03-18)
------------------

**Added**

* Added ``data`` parameter to ``Session.request``.

0.0.6 (2016-03-14)
------------------

**Fixed**

* prawcore objects can be pickled.

0.0.5 (2016-03-12)
------------------

**Added**

* 302 redirects result in a ``Redirect`` exception.

0.0.4 (2016-03-12)
------------------

**Added**

* Add a generic ``Forbidden`` exception for 403 responses without the
  ``www-authenticate`` header.

0.0.3 (2016-02-29)
------------------

**Added**

* Added ``params`` parameter to ``Session.request``.
* Log requests to the ``prawcore`` logger in debug mode.

0.0.2 (2016-02-21)
------------------

**Fixed**

* README.rst for display purposes on pypi.

0.0.1 (2016-02-17) [YANKED]
---------------------------

**Added**

* Dynamic rate limiting based on reddit's response headers.
* Authorization URL generation.
* Retrieval of access and refresh tokens from authorization grants.
* Access and refresh token revocation.
* Retrieval of read-only access tokens.
* Retrieval of script-app tokens.
* Three examples in the ``examples/`` directory.
