"""Prepare pytest."""

import os
import socket
import time
import asyncio
from base64 import b64encode
from sys import platform, modules

import requests
import niquests
import urllib3

# betamax is tied to Requests
# and Niquests is almost entirely compatible with it.
# we can fool it without effort.
modules["requests"] = niquests
modules["requests.adapters"] = niquests.adapters
modules["requests.models"] = niquests.models
modules["requests.exceptions"] = niquests.exceptions
modules["requests.packages.urllib3"] = urllib3

# niquests no longer have a compat submodule
# but betamax need it. no worries, as betamax
# explicitly need requests, we'll give it to him.
modules["requests.compat"] = requests.compat

# doing the import now will make betamax working with Niquests!
# no extra effort.
import betamax

# the base mock does not implement close(), which is required
# for our HTTP client. No biggy.
betamax.mock_response.MockHTTPResponse.close = lambda _: None

import pytest

from prawcore import Requestor, TrustedAuthenticator, UntrustedAuthenticator
from prawcore import (
    AsyncRequestor,
    AsyncTrustedAuthenticator,
    AsyncUntrustedAuthenticator,
)


@pytest.fixture(autouse=True)
def patch_sleep(monkeypatch):
    """Auto patch sleep to speed up tests."""

    def _sleep(*_, **__):
        """Dud sleep function."""
        pass

    monkeypatch.setattr(time, "sleep", value=_sleep)


@pytest.fixture(autouse=True)
def patch_async_sleep(monkeypatch):
    """Auto patch sleep to speed up tests."""

    async def _sleep(*_, **__):
        """Dud sleep function."""
        pass

    monkeypatch.setattr(asyncio, "sleep", value=_sleep)


@pytest.fixture
def image_path():
    """Return path to image."""

    def _get_path(name):
        """Return path to image."""
        return os.path.join(os.path.dirname(__file__), "integration", "files", name)

    return _get_path


@pytest.fixture
def requestor():
    """Return path to image."""
    return Requestor("prawcore:test (by /u/bboe)")


@pytest.fixture
def async_requestor():
    return AsyncRequestor("prawcore:test (by /u/bboe)")


@pytest.fixture
def trusted_authenticator(requestor):
    """Return a TrustedAuthenticator instance."""
    return TrustedAuthenticator(
        requestor,
        pytest.placeholders.client_id,
        pytest.placeholders.client_secret,
    )


@pytest.fixture
def async_trusted_authenticator(async_requestor):
    """Return a TrustedAuthenticator instance."""
    return AsyncTrustedAuthenticator(
        async_requestor,
        pytest.placeholders.client_id,
        pytest.placeholders.client_secret,
    )


@pytest.fixture
def untrusted_authenticator(requestor):
    """Return an UntrustedAuthenticator instance."""
    return UntrustedAuthenticator(requestor, pytest.placeholders.client_id)


@pytest.fixture
def async_untrusted_authenticator(async_requestor):
    """Return an UntrustedAuthenticator instance."""
    return AsyncUntrustedAuthenticator(async_requestor, pytest.placeholders.client_id)


def env_default(key):
    """Return environment variable or placeholder string."""
    return os.environ.get(
        f"PRAWCORE_{key.upper()}",
        "http://localhost:8080" if key == "redirect_uri" else f"fake_{key}",
    )


def pytest_configure(config):
    pytest.placeholders = Placeholders(placeholders)
    config.addinivalue_line(
        "markers", "add_placeholder: Define an additional placeholder for the cassette."
    )
    config.addinivalue_line(
        "markers", "cassette_name: Name of cassette to use for test."
    )
    config.addinivalue_line(
        "markers", "recorder_kwargs: Arguments to pass to the recorder."
    )


def two_factor_callback():
    """Return an OTP code."""
    return None


class Placeholders:
    def __init__(self, _dict):
        self.__dict__ = _dict


placeholders = {
    x: env_default(x)
    for x in (
        "client_id client_secret password permanent_grant_code temporary_grant_code"
        " redirect_uri refresh_token user_agent username"
    ).split()
}

if (
    placeholders["client_id"] != "fake_client_id"
    and placeholders["client_secret"] == "fake_client_secret"
):
    placeholders["basic_auth"] = b64encode(
        f"{placeholders['client_id']}:".encode("utf-8")
    ).decode("utf-8")
else:
    placeholders["basic_auth"] = b64encode(
        f"{placeholders['client_id']}:{placeholders['client_secret']}".encode("utf-8")
    ).decode("utf-8")


if platform == "darwin":  # Work around issue with betamax on OS X
    socket.gethostbyname = lambda x: "127.0.0.1"
