"""prawcore Integration test suite."""
from __future__ import annotations

import base64
import io
import os

import betamax
import pytest
from betamax.cassette import Cassette, Interaction
from betamax.util import body_io

from niquests import PreparedRequest, Response

from niquests.adapters import AsyncHTTPAdapter
from niquests.utils import _swap_context

try:
    from urllib3 import AsyncHTTPResponse, HTTPHeaderDict
    from urllib3.backend._async import AsyncLowLevelResponse
except ImportError:
    from urllib3_future import AsyncHTTPResponse, HTTPHeaderDict
    from urllib3_future.backend._async import AsyncLowLevelResponse

CASSETTES_PATH = "tests/integration/cassettes"
existing_cassettes = set()
used_cassettes = set()


@pytest.mark.asyncio
class AsyncIntegrationTest:
    """Base class for prawcore integration tests."""

    @pytest.fixture(autouse=True)
    def inject_fake_async_response(self, cassette_name, monkeypatch):
        """betamax does not support Niquests async capabilities.
        This fixture is made to compensate for this missing feature.
        """
        cassette_base_dir = os.path.join(os.path.dirname(__file__), "..", "cassettes")
        cassette = Cassette(cassette_name, serialization_format="json", cassette_library_dir=cassette_base_dir)
        cassette.match_options.update({"method"})

        def patch_add_urllib3_response(serialized, response, headers):
            """This function is patched so that we can construct a proper async dummy response."""
            if 'base64_string' in serialized['body']:
                body = io.BytesIO(
                    base64.b64decode(serialized['body']['base64_string'].encode())
                )
            else:
                body = body_io(**serialized['body'])

            async def fake_inner_read(*args) -> tuple[bytes, bool, HTTPHeaderDict | None]:
                """Fake the async iter socket read from AsyncHTTPConnection down in urllib3-future."""
                nonlocal body
                return body.getvalue(), True, None

            fake_llr = AsyncLowLevelResponse(
                method="GET",  # hardcoded, but we don't really care. It does not impact the tests.
                status=response.status_code,
                reason=response.reason,
                headers=headers,
                body=fake_inner_read,
                version=11,
            )

            h = AsyncHTTPResponse(
                body,
                status=response.status_code,
                reason=response.reason,
                headers=headers,
                original_response=fake_llr,
            )

            response.raw = h

        monkeypatch.setattr(betamax.util, "add_urllib3_response", patch_add_urllib3_response)

        async def fake_send(_, *args, **kwargs) -> Response:
            nonlocal cassette

            prep_request: PreparedRequest = args[0]

            interaction: Interaction | None = cassette.find_match(prep_request)

            if interaction:
                # betamax can generate a requests.Response
                # from a matched interaction.
                # three caveats:
                #   first: not async compatible
                #   second: we need to output niquests.AsyncResponse first
                #   third: the underlying HTTPResponse is sync bound

                resp = interaction.as_response()
                # Niquests have two kind of responses in async mode.
                #   A) Response (in case stream=False)
                #   B) AsyncResponse (in case stream=True)
                _swap_context(resp)

                return resp

            raise Exception("no match in cassettes for this request.")

        AsyncHTTPAdapter.send = fake_send

    @pytest.fixture
    def cassette_name(self, request):
        """Return the name of the cassette to use."""
        marker = request.node.get_closest_marker("cassette_name")
        if marker is None:
            return (
                f"{request.cls.__name__}.{request.node.name}"
                if request.cls
                else request.node.name
            )
        return marker.args[0]
