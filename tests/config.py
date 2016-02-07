"""Constants for the prawcore test suite."""

import os
from base64 import b64encode
from betamax import Betamax
from betamax_serializers import pretty_json

CLIENT_ID = os.environ.get('PRAWCORE_CLIENT_ID', 'fake_client_id')
CLIENT_SECRET = os.environ.get('PRAWCORE_CLIENT_SECRET', 'fake_client_secret')
REFRESH_TOKEN = os.environ.get('PRAWCORE_REFRESH_TOKEN', 'fake_refresh_token')


def b64_string(input_string):
    """Return a base64 encoded string (not bytes) from input_string."""
    return b64encode(input_string.encode('utf-8')).decode('utf-8')


Betamax.register_serializer(pretty_json.PrettyJSONSerializer)

with Betamax.configure() as config:
    if os.getenv('TRAVIS'):
        config.default_cassette_options['record_mode'] = 'none'
    config.cassette_library_dir = 'tests/cassettes'
    config.default_cassette_options['serialize_with'] = 'prettyjson'
    config.define_cassette_placeholder('<CLIENT_ID>', CLIENT_ID)
    config.define_cassette_placeholder('<CLIENT_SECRET>', CLIENT_SECRET)
    config.define_cassette_placeholder('<REFRESH_TOKEN>', REFRESH_TOKEN)
    config.define_cassette_placeholder('<BASIC_AUTH>', b64_string(
        '{}:{}'.format(CLIENT_ID, CLIENT_SECRET)))
