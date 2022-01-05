#!/usr/bin/env python

"""This example shows how simple in-memory caching can be used.

Demonstrates the use of custom sessions with :class:`Requestor`. It's an adaptation of
``read_only_auth_trophies.py``.

"""

import os
import sys

import requests

import prawcore


class CachingSession(requests.Session):
    """Cache GETs in memory.

    Toy example of custom session to showcase the ``session`` parameter of
    :class:`Requestor`.

    """

    get_cache = {}

    def request(self, method, url, params=None, **kwargs):
        """Perform a request, or return a cached response if available."""
        params_key = tuple(params.items()) if params else ()
        if method.upper() == "GET":
            if (url, params_key) in self.get_cache:
                print("Returning cached response for:", method, url, params)
                return self.get_cache[(url, params_key)]
        result = super().request(method, url, params, **kwargs)
        if method.upper() == "GET":
            self.get_cache[(url, params_key)] = result
            print("Adding entry to the cache:", method, url, params)
        return result


def main():
    """Provide the program's entry point when directly executed."""
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} USERNAME")
        return 1

    caching_requestor = prawcore.Requestor(
        "prawcore_device_id_auth_example", session=CachingSession()
    )
    authenticator = prawcore.TrustedAuthenticator(
        caching_requestor,
        os.environ["PRAWCORE_CLIENT_ID"],
        os.environ["PRAWCORE_CLIENT_SECRET"],
    )
    authorizer = prawcore.ReadOnlyAuthorizer(authenticator)
    authorizer.refresh()

    user = sys.argv[1]
    with prawcore.session(authorizer) as session:
        data1 = session.request("GET", f"/api/v1/user/{user}/trophies")

    with prawcore.session(authorizer) as session:
        data2 = session.request("GET", f"/api/v1/user/{user}/trophies")

    for trophy in data1["data"]["trophies"]:
        description = trophy["data"]["description"]
        print(
            "Original:",
            trophy["data"]["name"] + (f" ({description})" if description else ""),
        )

    for trophy in data2["data"]["trophies"]:
        description = trophy["data"]["description"]
        print(
            "Cached:",
            trophy["data"]["name"] + (f" ({description})" if description else ""),
        )
    print(
        "----\nCached == Original:",
        data2["data"]["trophies"] == data2["data"]["trophies"],
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
