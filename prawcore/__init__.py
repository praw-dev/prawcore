"""prawcore: Low-level communication layer for PRAW 4+."""

import logging
from .sessions import Session, session  # noqa


__version__ = '0.0.1a1'


logging.getLogger(__package__).addHandler(logging.NullHandler())
