.. _main_page:

prawcore
========

.. image:: https://img.shields.io/pypi/v/prawcore.svg
    :alt: Latest prawcore Version
    :target: https://pypi.python.org/pypi/prawcore

.. image:: https://img.shields.io/pypi/pyversions/prawcore
    :alt: Supported Python Versions
    :target: https://pypi.python.org/pypi/prawcore

.. image:: https://img.shields.io/pypi/dm/prawcore
    :alt: PyPI - Downloads - Monthly
    :target: https://pypi.python.org/pypi/prawcore

.. image:: https://github.com/praw-dev/prawcore/actions/workflows/ci.yml/badge.svg?event=push
    :alt: GitHub Actions Status
    :target: https://github.com/praw-dev/prawcore/actions/workflows/ci.yml

.. image:: https://coveralls.io/repos/github/praw-dev/prawcore/badge.svg
    :alt: Coveralls Coverage
    :target: https://coveralls.io/github/praw-dev/prawcore

.. image:: https://api.securityscorecards.dev/projects/github.com/praw-dev/prawcore/badge
    :alt: OpenSSF Scorecard
    :target: https://api.securityscorecards.dev/projects/github.com/praw-dev/prawcore

.. image:: https://img.shields.io/badge/Contributor%20Covenant-v2.0%20adopted-ff69b4.svg
    :alt: Contributor Covenant
    :target: https://github.com/praw-dev/.github/blob/main/CODE_OF_CONDUCT.md

.. image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white
    :alt: pre-commit
    :target: https://github.com/pre-commit/pre-commit

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :alt: Black code style
    :target: https://github.com/psf/black

prawcore is a low-level communication layer used by PRAW 4+.

Installation
------------

Install prawcore using ``pip`` via:

.. code-block:: console

    pip install prawcore

Execution Example
-----------------

The following example demonstrates how to use prawcore to obtain the list of trophies
for a given user using the script-app type. This example assumes you have the
environment variables ``PRAWCORE_CLIENT_ID`` and ``PRAWCORE_CLIENT_SECRET`` set to the
appropriate values for your application.

.. code-block:: python

    #!/usr/bin/env python
    import os
    import pprint
    import prawcore

    authenticator = prawcore.TrustedAuthenticator(
        prawcore.Requestor("YOUR_VALID_USER_AGENT"),
        os.environ["PRAWCORE_CLIENT_ID"],
        os.environ["PRAWCORE_CLIENT_SECRET"],
    )
    authorizer = prawcore.ReadOnlyAuthorizer(authenticator)
    authorizer.refresh()

    with prawcore.session(authorizer) as session:
        pprint.pprint(session.request("GET", "/api/v1/user/bboe/trophies"))

Save the above as ``trophies.py`` and then execute via:

.. code-block:: console

    python trophies.py

Additional examples can be found at:
https://github.com/praw-dev/prawcore/tree/main/examples

Or! with async/await!

.. code-block:: python

    #!/usr/bin/env python
    import os
    import pprint
    import asyncio
    import prawcore


    async def main():
        authenticator = prawcore.AsyncTrustedAuthenticator(
            prawcore.Requestor("YOUR_VALID_USER_AGENT"),
            os.environ["PRAWCORE_CLIENT_ID"],
            os.environ["PRAWCORE_CLIENT_SECRET"],
        )
        authorizer = prawcore.AsyncReadOnlyAuthorizer(authenticator)
        await authorizer.refresh()

        async with prawcore.async_session(authorizer) as session:
            pprint.pprint(await session.request("GET", "/api/v1/user/bboe/trophies"))


    asyncio.run(main())

Depending on prawcore
---------------------

prawcore follows `semantic versioning <https://semver.org/>`_ with the exception that
deprecations will not be preceded by a minor release. In essence, expect only major
versions to introduce breaking changes to prawcore's public interface. As a result, if
you depend on prawcore then it is a good idea to specify not only the minimum version of
prawcore your package requires, but to also limit the major version.

Below are two examples of how you may want to specify your prawcore dependency:

setup.py
~~~~~~~~

.. code-block:: python

    setup(..., install_requires=["prawcore >=0.1, <1"], ...)

requirements.txt
~~~~~~~~~~~~~~~~

.. code-block:: text

    prawcore >=1.5.1, <2
