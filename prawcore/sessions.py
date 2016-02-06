"""prawcore.sessions: Provides prawcore.Session and prawcore.session."""

import requests


class Session(object):
    """The low-level connection interface to reddit's API."""

    def __init__(self, authorizer=None):
        """Preprare the connection to reddit's API.

        :param authorizer: An instance of :class:`Authorizer`.

        """
        self.authorizer = authorizer
        self._session = requests.Session()

    def __enter__(self):
        """Allow this object to be used as a context manager."""
        return self

    def __exit__(self, *_args):
        """Allow this object to be used as a context manager."""
        self.close()

    def close(self):
        """Close the session and perform any clean up."""
        self._session.close()


def session(authorizer=None):
    """Return a :class:`Session` instance.

    :param authorizer: An instance of :class:`Authorizer`.

    """
    return Session(authorizer=authorizer)
