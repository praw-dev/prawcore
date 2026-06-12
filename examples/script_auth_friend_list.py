#!/usr/bin/env python

"""script_auth_friend_list.py outputs the authenticated user's list of friends.

This program demonstrates the use of ``prawcore.ScriptAuthorizer``, which enables those
listed as a developer of the application to authenticate using their username and
password.

"""

import os
import sys

import prawcore


def main():
    """Provide the program's entry point when directly executed."""
    authenticator = prawcore.TrustedAuthenticator(
        client_id=os.environ["PRAWCORE_CLIENT_ID"],
        client_secret=os.environ["PRAWCORE_CLIENT_SECRET"],
        requestor=prawcore.Requestor(user_agent="prawcore_script_auth_example"),
    )
    authorizer = prawcore.ScriptAuthorizer(
        authenticator=authenticator,
        username=os.environ["PRAWCORE_USERNAME"],
        password=os.environ["PRAWCORE_PASSWORD"],
    )
    authorizer.refresh()

    with prawcore.session(authorizer=authorizer) as session:
        data = session.request(method="GET", path="/api/v1/me/friends")

    for friend in data["data"]["children"]:
        print(friend["name"])

    return 0


if __name__ == "__main__":
    sys.exit(main())
