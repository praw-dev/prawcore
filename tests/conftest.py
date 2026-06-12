"""Prepare pytest."""

import os
import time
from base64 import b64encode

import pytest

from prawcore import Requestor, TrustedAuthenticator, UntrustedAuthenticator


@pytest.fixture(autouse=True)
def patch_sleep(monkeypatch):
    """Auto patch sleep to speed up tests."""

    def _sleep(*_, **__):
        """Dud sleep function."""

    monkeypatch.setattr(time, "sleep", value=_sleep)


@pytest.fixture
def requestor():
    """Return path to image."""
    return Requestor(user_agent="prawcore:test (by /u/bboe)")


@pytest.fixture
def trusted_authenticator(requestor):
    """Return a TrustedAuthenticator instance."""
    return TrustedAuthenticator(
        requestor,
        placeholders.client_id,
        placeholders.client_secret,
    )


@pytest.fixture
def untrusted_authenticator(requestor):
    """Return an UntrustedAuthenticator instance."""
    return UntrustedAuthenticator(requestor, placeholders.client_id)


def env_default(key):
    """Return environment variable or placeholder string."""
    return os.environ.get(
        f"PRAWCORE_{key.upper()}",
        "http://localhost:8080" if key == "redirect_uri" else f"fake_{key}",
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "cassette_name: Name of cassette to use for test.")
    config.addinivalue_line("markers", "recorder_kwargs: Arguments to pass to the recorder.")


class Placeholders:
    access_token: str
    basic_auth: str
    client_id: str
    client_secret: str
    password: str
    permanent_grant_code: str
    redirect_uri: str
    refresh_token: str
    temporary_grant_code: str
    user_agent: str
    username: str

    def __init__(self, _dict):
        self.__dict__ = _dict


placeholder_values = {
    x: env_default(x)
    for x in [
        "client_id",
        "client_secret",
        "password",
        "permanent_grant_code",
        "temporary_grant_code",
        "redirect_uri",
        "refresh_token",
        "user_agent",
        "username",
    ]
}

if (
    placeholder_values["client_id"] != "fake_client_id" and placeholder_values["client_secret"] == "fake_client_secret"
):  # pragma: no cover
    placeholder_values["basic_auth"] = b64encode(f"{placeholder_values['client_id']}:".encode()).decode("utf-8")
else:
    placeholder_values["basic_auth"] = b64encode(
        f"{placeholder_values['client_id']}:{placeholder_values['client_secret']}".encode(),
    ).decode("utf-8")

placeholders = Placeholders(placeholder_values)
