"""Constants for the prawcore test suite."""

import os
from base64 import b64encode
from betamax import Betamax
from betamax_matchers.json_body import JSONBodyMatcher
from betamax_serializers import pretty_json
from prawcore import Requestor

CLIENT_ID = os.environ.get("PRAWCORE_CLIENT_ID", "fake_client_id")
CLIENT_SECRET = os.environ.get("PRAWCORE_CLIENT_SECRET", "fake_client_secret")
PASSWORD = os.environ.get("PRAWCORE_PASSWORD", "fake_password")
PERMANENT_GRANT_CODE = os.environ.get(
    "PRAWCORE_PERMANENT_GRANT_CODE", "fake_perm_code"
)
REDIRECT_URI = os.environ.get("PRAWCORE_REDIRECT_URI", "http://localhost:8080")
REFRESH_TOKEN = os.environ.get("PRAWCORE_REFRESH_TOKEN", "fake_refresh_token")
TEMPORARY_GRANT_CODE = os.environ.get(
    "PRAWCORE_TEMPORARY_GRANT_CODE", "fake_temp_code"
)
USERNAME = os.environ.get("PRAWCORE_USERNAME", "fake_username")


REQUESTOR = Requestor("prawcore:test (by /u/bboe)")


def b64_string(input_string):
    """Return a base64 encoded string (not bytes) from input_string."""
    return b64encode(input_string.encode("utf-8")).decode("utf-8")


Betamax.register_request_matcher(JSONBodyMatcher)
Betamax.register_serializer(pretty_json.PrettyJSONSerializer)

with Betamax.configure() as config:
    if os.getenv("TRAVIS"):
        config.default_cassette_options["record_mode"] = "none"
    config.cassette_library_dir = "tests/cassettes"
    config.default_cassette_options["serialize_with"] = "prettyjson"
    config.default_cassette_options["match_requests_on"].append("body")
    config.define_cassette_placeholder(
        "<BASIC_AUTH>", b64_string("{}:{}".format(CLIENT_ID, CLIENT_SECRET))
    )
    config.define_cassette_placeholder("<CLIENT_ID>", CLIENT_ID)
    config.define_cassette_placeholder("<CLIENT_SECRET>", CLIENT_SECRET)
    config.define_cassette_placeholder("<PASSWORD>", PASSWORD)
    config.define_cassette_placeholder("<PERM_CODE>", PERMANENT_GRANT_CODE)
    config.define_cassette_placeholder("<REFRESH_TOKEN>", REFRESH_TOKEN)
    config.define_cassette_placeholder("<TEMP_CODE>", TEMPORARY_GRANT_CODE)
    config.define_cassette_placeholder("<USERNAME>", USERNAME)
