#!/usr/bin/env python

"""script_auth_friend_list.py outputs the authenticated user's list of friends.

This program demonstrates the use of ``prawcore.ScriptAuthorizer``, which
enables those listed as a developer of the application to authenticate using
their username and password.

"""
import os
import prawcore
import sys


def main():
    """Provide the program's entry point when directly executed."""
    authenticator = prawcore.Authenticator(
        prawcore.Requestor('prawcore_script_auth_example'),
        os.environ['PRAWCORE_CLIENT_ID'],
        os.environ['PRAWCORE_CLIENT_SECRET'])
    authorizer = prawcore.ScriptAuthorizer(authenticator,
                                           os.environ['PRAWCORE_USERNAME'],
                                           os.environ['PRAWCORE_PASSWORD'])
    authorizer.refresh()

    with prawcore.session(authorizer) as session:
        data = session.request('GET', '/api/v1/me/friends')

    for friend in data['data']['children']:
        print(friend['name'])

    return 0


if __name__ == '__main__':
    sys.exit(main())
