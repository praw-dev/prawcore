"""Test for prawcore.Sessions module."""

import logging
from json import dumps

import pytest
import pytest_asyncio

import prawcore

from . import AsyncIntegrationTest


class TestSession(AsyncIntegrationTest):
    @pytest_asyncio.fixture
    async def async_readonly_authorizer(self, async_trusted_authenticator):
        authorizer = prawcore.AsyncReadOnlyAuthorizer(async_trusted_authenticator)
        await authorizer.refresh()
        return authorizer

    @pytest_asyncio.fixture
    async def async_script_authorizer(self, async_trusted_authenticator):
        authorizer = prawcore.AsyncScriptAuthorizer(
            async_trusted_authenticator,
            pytest.placeholders.username,
            pytest.placeholders.password,
        )
        await authorizer.refresh()
        return authorizer

    async def test_request__accepted(self, async_script_authorizer, caplog):
        caplog.set_level(logging.DEBUG)
        session = prawcore.AsyncSession(async_script_authorizer)
        await session.request("POST", "api/read_all_messages")
        found_message = False
        for package, level, message in caplog.record_tuples:
            if (
                package == "prawcore._async"
                and level == logging.DEBUG
                and "Response: 202 (2 bytes)" in message
            ):
                found_message = True
        assert found_message, f"'Response: 202 (2 bytes)' in {caplog.record_tuples}"

    async def test_request__bad_gateway(self, async_readonly_authorizer):
        session = prawcore.AsyncSession(async_readonly_authorizer)
        with pytest.raises(prawcore.ServerError) as exception_info:
            await session.request("GET", "/")
        assert exception_info.value.response.status_code == 502

    async def test_request__bad_json(self, async_script_authorizer):
        session = prawcore.AsyncSession(async_script_authorizer)
        with pytest.raises(prawcore.BadJSON) as exception_info:
            await session.request("GET", "/")
        assert len(exception_info.value.response.content) == 92

    async def test_request__bad_request(self, async_script_authorizer):
        session = prawcore.AsyncSession(async_script_authorizer)
        with pytest.raises(prawcore.BadRequest) as exception_info:
            await session.request(
                "PUT", "/api/v1/me/friends/spez", data='{"note": "prawcore"}'
            )
        assert "reason" in exception_info.value.response.json()

    async def test_request__cloudflare_connection_timed_out(
        self, async_readonly_authorizer
    ):
        session = prawcore.AsyncSession(async_readonly_authorizer)
        with pytest.raises(prawcore.ServerError) as exception_info:
            await session.request("GET", "/")
            await session.request("GET", "/")
            await session.request("GET", "/")
        assert exception_info.value.response.status_code == 522

    async def test_request__cloudflare_unknown_error(self, async_readonly_authorizer):
        session = prawcore.AsyncSession(async_readonly_authorizer)
        with pytest.raises(prawcore.ServerError) as exception_info:
            await session.request("GET", "/")
            await session.request("GET", "/")
            await session.request("GET", "/")
        assert exception_info.value.response.status_code == 520

    async def test_request__conflict(self, async_script_authorizer):
        session = prawcore.AsyncSession(async_script_authorizer)
        previous = "f0214574-430d-11e7-84ca-1201093304fa"
        with pytest.raises(prawcore.Conflict) as exception_info:
            await session.request(
                "POST",
                "/r/ThirdRealm/api/wiki/edit",
                data={
                    "content": "New text",
                    "page": "index",
                    "previous": previous,
                },
            )
        assert exception_info.value.response.status_code == 409

    async def test_request__created(self, async_script_authorizer):
        session = prawcore.AsyncSession(async_script_authorizer)
        response = await session.request("PUT", "/api/v1/me/friends/spez", data="{}")
        assert "name" in response

    async def test_request__forbidden(self, async_script_authorizer):
        session = prawcore.AsyncSession(async_script_authorizer)
        with pytest.raises(prawcore.Forbidden):
            await session.request("GET", "/user/spez/gilded/given")

    async def test_request__gateway_timeout(self, async_readonly_authorizer):
        session = prawcore.AsyncSession(async_readonly_authorizer)
        with pytest.raises(prawcore.ServerError) as exception_info:
            await session.request("GET", "/")
        assert exception_info.value.response.status_code == 504

    async def test_request__get(self, async_readonly_authorizer):
        session = prawcore.AsyncSession(async_readonly_authorizer)
        params = {"limit": 100}
        response = await session.request("GET", "/", params=params)
        assert isinstance(response, dict)
        assert len(params) == 1
        assert response["kind"] == "Listing"

    async def test_request__internal_server_error(self, async_readonly_authorizer):
        session = prawcore.AsyncSession(async_readonly_authorizer)
        with pytest.raises(prawcore.ServerError) as exception_info:
            await session.request("GET", "/")
        assert exception_info.value.response.status_code == 500

    async def test_request__no_content(self, async_script_authorizer):
        session = prawcore.AsyncSession(async_script_authorizer)
        response = await session.request("DELETE", "/api/v1/me/friends/spez")
        assert response is None

    async def test_request__not_found(self, async_script_authorizer):
        session = prawcore.AsyncSession(async_script_authorizer)
        with pytest.raises(prawcore.NotFound):
            await session.request("GET", "/r/reddit_api_test/wiki/invalid")

    async def test_request__okay_with_0_byte_content(self, async_script_authorizer):
        session = prawcore.AsyncSession(async_script_authorizer)
        data = {"model": dumps({"name": "redditdev"})}
        path = f"/api/multi/user/{pytest.placeholders.username}/m/praw_x5g968f66a/r/redditdev"
        response = await session.request("DELETE", path, data=data)
        assert response == ""

    @pytest.mark.recorder_kwargs(match_requests_on=["method", "uri", "body"])
    async def test_request__patch(self, async_script_authorizer):
        session = prawcore.AsyncSession(async_script_authorizer)
        json = {"lang": "ja", "num_comments": 123}
        response = await session.request("PATCH", "/api/v1/me/prefs", json=json)
        assert response["lang"] == "ja"
        assert response["num_comments"] == 123

    async def test_request__post(self, async_script_authorizer):
        session = prawcore.AsyncSession(async_script_authorizer)
        data = {
            "kind": "self",
            "sr": "reddit_api_test",
            "text": "Test!",
            "title": "A Test from PRAWCORE.",
        }
        key_count = len(data)
        response = await session.request("POST", "/api/submit", data=data)
        assert "a_test_from_prawcore" in response["json"]["data"]["url"]
        assert key_count == len(data)  # Ensure data is untouched

    @pytest.mark.recorder_kwargs(match_requests_on=["uri", "method"])
    async def test_request__post__with_files(self, async_script_authorizer):
        session = prawcore.AsyncSession(async_script_authorizer)
        data = {"upload_type": "header"}
        with open("tests/integration/files/white-square.png", "rb") as fp:
            files = {"file": fp}
            response = await session.request(
                "POST",
                "/r/reddit_api_test/api/upload_sr_img",
                data=data,
                files=files,
            )
        assert "img_src" in response

    async def test_request__raw_json(self, async_readonly_authorizer):
        session = prawcore.AsyncSession(async_readonly_authorizer)
        response = await session.request(
            "GET",
            "/r/reddit_api_test/comments/45xjdr/want_raw_json_test/",
        )
        assert (
            "WANT_RAW_JSON test: < > &"
            == response[0]["data"]["children"][0]["data"]["title"]
        )

    async def test_request__redirect(self, async_readonly_authorizer):
        session = prawcore.AsyncSession(async_readonly_authorizer)
        with pytest.raises(prawcore.Redirect) as exception_info:
            await session.request("GET", "/r/random")
        assert exception_info.value.path.startswith("/r/")

    async def test_request__redirect_301(self, async_readonly_authorizer):
        session = prawcore.AsyncSession(async_readonly_authorizer)
        with pytest.raises(prawcore.Redirect) as exception_info:
            await session.request("GET", "t/bird")
        assert exception_info.value.path == "/r/t:bird/"

    async def test_request__service_unavailable(self, async_readonly_authorizer):
        session = prawcore.AsyncSession(async_readonly_authorizer)
        with pytest.raises(prawcore.ServerError) as exception_info:
            await session.request("GET", "/")
            await session.request("GET", "/")
            await session.request("GET", "/")
        assert exception_info.value.response.status_code == 503

    async def test_request__too__many_requests__with_retry_headers(
        self, async_readonly_authorizer
    ):
        session = prawcore.AsyncSession(async_readonly_authorizer)
        session._requestor._http.headers.update(
            {"User-Agent": "python-requests/2.25.1"}
        )
        with pytest.raises(prawcore.TooManyRequests) as exception_info:
            await session.request("GET", "/api/v1/me")
        assert exception_info.value.response.status_code == 429
        assert exception_info.value.response.headers.get("retry-after")
        assert exception_info.value.response.reason == "Too Many Requests"
        assert str(exception_info.value).startswith(
            "received 429 HTTP response. Please wait at least"
        )
        assert exception_info.value.message.startswith("\n<!doctype html>")

    async def test_request__too__many_requests__without_retry_headers(
        self, async_requestor
    ):
        async_requestor._http.headers.update({"User-Agent": "python-requests/2.25.1"})
        authorizer = prawcore.AsyncReadOnlyAuthorizer(
            prawcore.AsyncTrustedAuthenticator(
                async_requestor,
                pytest.placeholders.client_id,
                pytest.placeholders.client_secret,
            )
        )
        with pytest.raises(prawcore.exceptions.ResponseException) as exception_info:
            await authorizer.refresh()
        assert exception_info.value.response.status_code == 429
        assert not exception_info.value.response.headers.get("retry-after")
        assert exception_info.value.response.reason == "Too Many Requests"
        assert exception_info.value.response.json() == {
            "message": "Too Many Requests",
            "error": 429,
        }

    @pytest.mark.recorder_kwargs(match_requests_on=["uri", "method"])
    async def test_request__too_large(self, async_script_authorizer):
        session = prawcore.AsyncSession(async_script_authorizer)
        data = {"upload_type": "header"}
        with open("tests/integration/files/too_large.jpg", "rb") as fp:
            files = {"file": fp}
            with pytest.raises(prawcore.TooLarge) as exception_info:
                await session.request(
                    "POST",
                    "/r/reddit_api_test/api/upload_sr_img",
                    data=data,
                    files=files,
                )
        assert exception_info.value.response.status_code == 413

    async def test_request__unavailable_for_legal_reasons(
        self, async_readonly_authorizer
    ):
        session = prawcore.AsyncSession(async_readonly_authorizer)
        exception_class = prawcore.UnavailableForLegalReasons
        with pytest.raises(exception_class) as exception_info:
            await session.request("GET", "/")
        assert exception_info.value.response.status_code == 451

    async def test_request__unsupported_media_type(self, async_script_authorizer):
        session = prawcore.AsyncSession(async_script_authorizer)
        exception_class = prawcore.SpecialError
        data = {
            "content": "type: submission\naction: upvote",
            "page": "config/automoderator",
        }
        with pytest.raises(exception_class) as exception_info:
            await session.request("POST", "r/ttft/api/wiki/edit/", data=data)
        assert exception_info.value.response.status_code == 415

    async def test_request__uri_too_long(self, async_readonly_authorizer):
        session = prawcore.AsyncSession(async_readonly_authorizer)
        path_start = "/api/morechildren?link_id=t3_n7r3uz&children="
        with open("tests/integration/files/comment_ids.txt") as fp:
            ids = fp.read()
        with pytest.raises(prawcore.URITooLong) as exception_info:
            await session.request("GET", (path_start + ids)[:9996])
        assert exception_info.value.response.status_code == 414

    async def test_request__with_insufficient_scope(self, async_trusted_authenticator):
        authorizer = prawcore.AsyncAuthorizer(
            async_trusted_authenticator, refresh_token=pytest.placeholders.refresh_token
        )
        await authorizer.refresh()
        session = prawcore.AsyncSession(authorizer)
        with pytest.raises(prawcore.InsufficientScope):
            await session.request(
                "GET",
                "/api/v1/me",
            )

    async def test_request__with_invalid_access_token(
        self, async_untrusted_authenticator
    ):
        authorizer = prawcore.AsyncImplicitAuthorizer(
            async_untrusted_authenticator, None, 0, ""
        )
        session = prawcore.AsyncSession(authorizer)
        session._authorizer.access_token = "invalid"
        with pytest.raises(prawcore.InvalidToken):
            r = await session.request("get", "/")

    async def test_request__with_invalid_access_token__retry(
        self, async_readonly_authorizer
    ):
        session = prawcore.AsyncSession(async_readonly_authorizer)
        session._authorizer.access_token += "invalid"
        response = await session.request("GET", "/")
        assert isinstance(response, dict)
