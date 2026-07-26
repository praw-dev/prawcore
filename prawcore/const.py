"""Constants for the prawcore package."""

import os

ACCESS_TOKEN_PATH = "/api/v1/access_token"  # ruff:ignore[hardcoded-password-string]
AUTHORIZATION_PATH = "/api/v1/authorize"
NANOSECONDS = 1_000_000_000
REVOKE_TOKEN_PATH = "/api/v1/revoke_token"  # ruff:ignore[hardcoded-password-string]
TIMEOUT = float(
    os.environ.get(
        "PRAWCORE_TIMEOUT",
        os.environ.get("prawcore_timeout", "16"),  # ruff:ignore[uncapitalized-environment-variables]
    ),
)
WINDOW_SIZE = 600
