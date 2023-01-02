"""Prepare py.test."""
import os
import socket
import time
from base64 import b64encode
from sys import platform

import pytest

import prawcore
from prawcore import Requestor


@pytest.fixture(autouse=True)
def patch_sleep(monkeypatch):
    """Auto patch sleep to speed up tests."""

    def _sleep(*_, **__):
        """Dud sleep function."""
        return

    monkeypatch.setattr(time, "sleep", value=_sleep)


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
def trusted_authenticator(requestor):
    return prawcore.TrustedAuthenticator(
        requestor,
        pytest.placeholders.client_id,
        pytest.placeholders.client_secret,
    )


@pytest.fixture
def untrusted_authenticator(requestor):
    return prawcore.UntrustedAuthenticator(requestor, pytest.placeholders.client_id)


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


placeholders = {
    x: env_default(x)
    for x in (
        "client_id client_secret password permanent_grant_code temporary_grant_code"
        " redirect_uri refresh_token user_agent username"
    ).split()
}


placeholders["basic_auth"] = b64encode(
    f"{placeholders['client_id']}:{placeholders['client_secret']}".encode("utf-8")
).decode("utf-8")


class Placeholders:
    def __init__(self, _dict):
        self.__dict__ = _dict


if platform == "darwin":  # Work around issue with betamax on OS X
    socket.gethostbyname = lambda x: "127.0.0.1"
