#!/usr/bin/env python

"""This example demonstrates the flow for retrieving a refresh token.

In order for this example to work your application's redirect URI must be set
to http://localhost:65010/auth_callback.

This tool can be used to conveniently create refresh tokens for later use with
your web application OAuth2 credentials.

"""
import os
import sys

import prawcore


def main():
    """Provide the program's entry point when directly executed."""
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} SCOPE...")
        return 1

    authorizer = prawcore.LocalWSGIServerAuthorizer(
        prawcore.TrustedAuthenticator(
            prawcore.Requestor("prawcore_refresh_token_example"),
            os.environ["PRAWCORE_CLIENT_ID"],
            os.environ["PRAWCORE_CLIENT_SECRET"],
            "http://localhost:65010/auth_callback",
        ),
        sys.argv[1:],
        duration="permanent",
    )
    authorizer.authorize_local_server()
    print(f"Refresh token: {authorizer.refresh_token}")


if __name__ == "__main__":
    sys.exit(main())
