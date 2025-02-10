"""prawcore Integration test suite."""

import os
from urllib.parse import quote_plus

import betamax
import pytest
from betamax.cassette import Cassette

from ..utils import (
    PrettyJSONSerializer,
    ensure_integration_test,
    filter_access_token,
)

CASSETTES_PATH = "tests/integration/cassettes"
existing_cassettes = set()
used_cassettes = set()


class IntegrationTest:
    """Base class for prawcore integration tests."""

    @pytest.fixture(autouse=True, scope="session")
    def cassette_tracker(self):  # pragma: no cover
        """Track cassettes to ensure unused cassettes are not uploaded."""
        for cassette in os.listdir(CASSETTES_PATH):
            existing_cassettes.add(cassette[: cassette.rindex(".")])
        yield
        unused_cassettes = existing_cassettes - used_cassettes
        if unused_cassettes and os.getenv("ENSURE_NO_UNUSED_CASSETTES", "0") == "1":
            msg = f"The following cassettes are unused: {', '.join(unused_cassettes)}."
            raise AssertionError(msg)

    @pytest.fixture(autouse=True)
    def cassette(self, request, recorder, cassette_name):
        """Wrap a test in a Betamax cassette."""
        kwargs = {}
        for marker in request.node.iter_markers("recorder_kwargs"):
            for key, value in marker.kwargs.items():
                #  Don't overwrite existing values since function markers are provided
                #  before class markers.
                kwargs.setdefault(key, value)
        with recorder.use_cassette(cassette_name, **kwargs) as recorder_context:
            cassette = recorder_context.current_cassette
            yield recorder_context
            ensure_integration_test(cassette)
            used_cassettes.add(cassette_name)

    @pytest.fixture(autouse=True)
    def recorder(self, requestor):
        """Configure Betamax."""
        recorder = betamax.Betamax(requestor)
        recorder.register_serializer(PrettyJSONSerializer)
        with betamax.Betamax.configure() as config:
            config.cassette_library_dir = CASSETTES_PATH
            config.default_cassette_options["serialize_with"] = "prettyjson"
            config.before_record(callback=filter_access_token)
            for key, value in pytest.placeholders.__dict__.items():
                if key == "password":
                    value = quote_plus(value)  # noqa: PLW2901
                config.define_cassette_placeholder(f"<{key.upper()}>", value)
            yield recorder
            # since placeholders persist between tests
            Cassette.default_cassette_options["placeholders"] = []

    @pytest.fixture
    def cassette_name(self, request):
        """Return the name of the cassette to use."""
        marker = request.node.get_closest_marker("cassette_name")
        if marker is None:
            return f"{request.cls.__name__}.{request.node.name}" if request.cls else request.node.name
        return marker.args[0]
