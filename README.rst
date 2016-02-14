.. _main_page:

prawcore
========

.. image:: https://travis-ci.org/praw-dev/prawcore.svg?branch=master
           :target: https://travis-ci.org/praw-dev/prawcore
.. image:: https://coveralls.io/repos/github/praw-dev/prawcore/badge.svg?branch=master
           :target: https://coveralls.io/github/praw-dev/prawcore?branch=master


Notice: This package is in development and should not be used until this notice
is removed.

prawcore is a low-level communication layer for PRAW 4+.


Installation
------------

Install prawcore using ``pip`` via:

.. code-block:: bashsession

    pip install prawcore

Depending on prawcore
---------------------

prawcore follows `semantic versioning <http://semver.org/>`_ with the exception
that deprecations will not be preceded by a minor release. In essense, expect
only major versions to introduce breaking changes to prawcore's public
interface. As a result, if you depend on prawcore then it is a good idea to
specify not only the minimum version of prawcore your package requires, but to
also limit the major version.

Below are two examples of how you may want to specify your prawcore dependency:

setup.py
~~~~~~~~

.. code-block:: python

   setup(...,
         install_requires=['prawcore >=0.1, <1'],
         ...)

requirements.txt
~~~~~~~~~~~~~~~~

.. code-block:: text

   prawcore >=1.5.1, <2
