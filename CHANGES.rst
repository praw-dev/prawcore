Change Log
==========

prawcore follows `semantic versioning <http://semver.org/>`_ with the exception
that deprecations will not be announced by a minor release.

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
