"""Low-level communication layer for PRAW 4+."""

import logging

from prawcore import exceptions
from prawcore.auth import (
    Authorizer,
    DeviceIDAuthorizer,
    ImplicitAuthorizer,
    ReadOnlyAuthorizer,
    ScriptAuthorizer,
    TrustedAuthenticator,
    UntrustedAuthenticator,
)
from prawcore.exceptions import *  # noqa: F403
from prawcore.requestor import Requestor
from prawcore.sessions import Session, session

logging.getLogger(__package__).addHandler(logging.NullHandler())

__all__ = [
    "Authorizer",
    "DeviceIDAuthorizer",
    "ImplicitAuthorizer",
    "ReadOnlyAuthorizer",
    "Requestor",
    "ScriptAuthorizer",
    "Session",
    "TrustedAuthenticator",
    "UntrustedAuthenticator",
    "session",
]
__all__ += exceptions.__all__

__version__ = "4.0.1.dev0"
