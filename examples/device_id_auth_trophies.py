#!/usr/bin/env python

"""This example outputs a user's list of trophies.

This program demonstrates the use of ``prawcore.DeviceIDAuthorizer``.

"""

import os
import sys

import prawcore


def main():
    """Provide the program's entry point when directly executed."""
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} USERNAME")
        return 1

    authenticator = prawcore.UntrustedAuthenticator(
        prawcore.Requestor("prawcore_device_id_auth_example"),
        os.environ["PRAWCORE_CLIENT_ID"],
    )
    authorizer = prawcore.DeviceIDAuthorizer(authenticator)
    authorizer.refresh()

    user = sys.argv[1]
    with prawcore.session(authorizer) as session:
        data = session.request("GET", f"/api/v1/user/{user}/trophies")

    for trophy in data["data"]["trophies"]:
        description = trophy["data"]["description"]
        print(
            trophy["data"]["name"]
            + (f" ({description})" if description else "")
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
