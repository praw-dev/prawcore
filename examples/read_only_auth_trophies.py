#!/usr/bin/env python

"""This example outputs a user's list of trophies.

This program demonstrates the use of ``prawcore.ReadOnlyAuthorizer`` that does
not require an access token to make authenticated requests to reddit.

"""
import os
import prawcore
import sys


def main():
    """main is the program's entry point when directly executed."""
    if len(sys.argv) != 2:
        print('Usage: {} USERNAME'.format(sys.argv[0]))
        return 1

    authenticator = prawcore.Authenticator(
        os.environ['PRAWCORE_CLIENT_ID'],
        os.environ['PRAWCORE_CLIENT_SECRET'])
    authorizer = prawcore.ReadOnlyAuthorizer(authenticator)
    authorizer.refresh()

    user = sys.argv[1]
    url = 'https://oauth.reddit.com/api/v1/user/{}/trophies'.format(user)
    with prawcore.session(authorizer) as session:
        data = session.request('GET', url)

    for trophy in data['data']['trophies']:
        description = trophy['data']['description']
        print(trophy['data']['name'] +
              (' ({})'.format(description) if description else ''))

    return 0


if __name__ == '__main__':
    sys.exit(main())
