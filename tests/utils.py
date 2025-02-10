"""Pytest utils for integration tests."""

import json

import betamax
from betamax.serializers import JSONSerializer


def ensure_integration_test(cassette):
    if cassette.is_recording():
        is_integration_test = bool(cassette.interactions)
        action = "record"
    else:
        is_integration_test = any(interaction.used for interaction in cassette.interactions)
        action = "play back"
    message = f"Cassette did not {action} any requests. This test can be a unit test."
    assert is_integration_test, message


def filter_access_token(interaction, current_cassette):
    """Add Betamax placeholder to filter access token."""
    request_uri = interaction.data["request"]["uri"]
    response = interaction.data["response"]
    if "api/v1/access_token" not in request_uri or response["status"]["code"] != 200:
        return
    body = response["body"]["string"]
    for token_key in ["access", "refresh"]:
        try:
            token = json.loads(body)[f"{token_key}_token"]
        except (KeyError, TypeError, ValueError):
            continue
        current_cassette.placeholders.append(
            betamax.cassette.cassette.Placeholder(placeholder=f"<{token_key.upper()}_TOKEN>", replace=token)
        )


class PrettyJSONSerializer(JSONSerializer):
    name = "prettyjson"

    def serialize(self, cassette_data):
        return f"{json.dumps(cassette_data, sort_keys=True, indent=2)}\n"
