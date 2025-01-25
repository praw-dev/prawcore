"""Constants for the prawcore package."""

import os

ACCESS_TOKEN_PATH = "/api/v1/access_token"  # noqa: S105
AUTHORIZATION_PATH = "/api/v1/authorize"  # noqa: S105
NANOSECONDS = 1_000_000_000  # noqa: S105
REVOKE_TOKEN_PATH = "/api/v1/revoke_token"  # noqa: S105
TIMEOUT = float(
    os.environ.get(
        "PRAWCORE_TIMEOUT",
        os.environ.get("prawcore_timeout", 16),  # noqa: SIM112
    )
)
WINDOW_SIZE = 600
