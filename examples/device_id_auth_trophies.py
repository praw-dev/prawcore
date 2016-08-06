#!/usr/bin/env python

"""This example outputs a user's list of trophies.

This program demonstrates the use of ``prawcore.DeviceIDAuthorizer``.
"""

import os
import prawcore
import sys


def main():
    """Provide the program's entry point when directly executed."""
    if len(sys.argv) != 2:
        print('Usage: {} USERNAME'.format(sys.argv[0]))
        return 1

    authenticator = prawcore.Authenticator(
        prawcore.Requestor('prawcore_device_id_auth_example'),
        os.environ['PRAWCORE_CLIENT_ID'])
    authorizer = prawcore.DeviceIDAuthorizer(authenticator)
    authorizer.refresh()

    user = sys.argv[1]
    with prawcore.session(authorizer) as session:
        data = session.request('GET', '/api/v1/user/{}/trophies'.format(user))

    for trophy in data['data']['trophies']:
        description = trophy['data']['description']
        print(trophy['data']['name'] +
              (' ({})'.format(description) if description else ''))

    return 0


if __name__ == '__main__':
    sys.exit(main())
