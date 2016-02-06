"""prawcore: Low-level communication layer for PRAW 4+."""

import logging
from .const import __version__  # noqa
from .sessions import Session, session  # noqa


logging.getLogger(__package__).addHandler(logging.NullHandler())
