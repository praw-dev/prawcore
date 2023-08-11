"""Test for prawcore.Sessions module."""
import logging
from json import dumps

import pytest

import prawcore

from ..conftest import two_factor_callback
from . import IntegrationTest


class InvalidAuthorizer(prawcore.Authorizer):
    def __init__(self, requestor):
        super(InvalidAuthorizer, self).__init__(
            prawcore.TrustedAuthenticator(
                requestor,
                pytest.placeholders.client_id,
                pytest.placeholders.client_secret,
            )
        )

    def is_valid(self):
        return False


class TestSession(IntegrationTest):
    @pytest.fixture
    def readonly_authorizer(self, trusted_authenticator):
        authorizer = prawcore.ReadOnlyAuthorizer(trusted_authenticator)
        authorizer.refresh()
        return authorizer

    @pytest.fixture
    def script_authorizer(self, trusted_authenticator):
        authorizer = prawcore.ScriptAuthorizer(
            trusted_authenticator,
            pytest.placeholders.username,
            pytest.placeholders.password,
            two_factor_callback,
        )
        authorizer.refresh()
        return authorizer

    def test_request__accepted(self, script_authorizer, caplog):
        caplog.set_level(logging.DEBUG)
        session = prawcore.Session(script_authorizer)
        session.request("POST", "api/read_all_messages")
        found_message = False
        for package, level, message in caplog.record_tuples:
            if package == "prawcore" and level == logging.DEBUG and \
                    "Response: 202 (2 bytes)" in message:
                found_message = True
        assert \
            found_message, \
            f"'Response: 202 (2 bytes)' in {caplog.record_tuples}"

    def test_request__bad_gateway(self, readonly_authorizer):
        session = prawcore.Session(readonly_authorizer)
        with pytest.raises(prawcore.ServerError) as exception_info:
            session.request("GET", "/")
        assert exception_info.value.response.status_code == 502

    def test_request__bad_json(self, script_authorizer):
        session = prawcore.Session(script_authorizer)
        with pytest.raises(prawcore.BadJSON) as exception_info:
            session.request("GET", "/")
        assert len(exception_info.value.response.content) == 92

    def test_request__bad_request(self, script_authorizer):
        session = prawcore.Session(script_authorizer)
        with pytest.raises(prawcore.BadRequest) as exception_info:
            session.request(
                "PUT", "/api/v1/me/friends/spez", data='{"note": "prawcore"}'
            )
        assert "reason" in exception_info.value.response.json()

    def test_request__cloudflare_connection_timed_out(self, readonly_authorizer):
        session = prawcore.Session(readonly_authorizer)
        with pytest.raises(prawcore.ServerError) as exception_info:
            session.request("GET", "/")
            session.request("GET", "/")
            session.request("GET", "/")
        assert exception_info.value.response.status_code == 522

    def test_request__cloudflare_unknown_error(self, readonly_authorizer):
        session = prawcore.Session(readonly_authorizer)
        with pytest.raises(prawcore.ServerError) as exception_info:
            session.request("GET", "/")
            session.request("GET", "/")
            session.request("GET", "/")
        assert exception_info.value.response.status_code == 520

    def test_request__conflict(self, script_authorizer):
        session = prawcore.Session(script_authorizer)
        previous = "f0214574-430d-11e7-84ca-1201093304fa"
        with pytest.raises(prawcore.Conflict) as exception_info:
            session.request(
                "POST",
                "/r/ThirdRealm/api/wiki/edit",
                data={
                    "content": "New text",
                    "page": "index",
                    "previous": previous,
                },
            )
        assert exception_info.value.response.status_code == 409

    def test_request__created(self, script_authorizer):
        session = prawcore.Session(script_authorizer)
        response = session.request("PUT", "/api/v1/me/friends/spez", data="{}")
        assert "name" in response

    def test_request__forbidden(self, script_authorizer):
        session = prawcore.Session(script_authorizer)
        with pytest.raises(prawcore.Forbidden):
            session.request("GET", "/user/spez/gilded/given")

    def test_request__gateway_timeout(self, readonly_authorizer):
        session = prawcore.Session(readonly_authorizer)
        with pytest.raises(prawcore.ServerError) as exception_info:
            session.request("GET", "/")
        assert exception_info.value.response.status_code == 504

    def test_request__get(self, readonly_authorizer):
        session = prawcore.Session(readonly_authorizer)
        params = {"limit": 100}
        response = session.request("GET", "/", params=params)
        assert isinstance(response, dict)
        assert len(params) == 1
        assert response["kind"] == "Listing"

    def test_request__internal_server_error(self, readonly_authorizer):
        session = prawcore.Session(readonly_authorizer)
        with pytest.raises(prawcore.ServerError) as exception_info:
            session.request("GET", "/")
        assert exception_info.value.response.status_code == 500

    def test_request__no_content(self, script_authorizer):
        session = prawcore.Session(script_authorizer)
        response = session.request("DELETE", "/api/v1/me/friends/spez")
        assert response is None

    def test_request__not_found(self, script_authorizer):
        session = prawcore.Session(script_authorizer)
        with pytest.raises(prawcore.NotFound):
            session.request("GET", "/r/reddit_api_test/wiki/invalid")

    def test_request__okay_with_0_byte_content(self, script_authorizer):
        session = prawcore.Session(script_authorizer)
        data = {"model": dumps({"name": "redditdev"})}
        path = f"/api/multi/user/{pytest.placeholders.username}/m/praw_x5g968f66a/r/redditdev"
        response = session.request("DELETE", path, data=data)
        assert response == ""

    @pytest.mark.recorder_kwargs(match_requests_on=["method", "uri", "body"])
    def test_request__patch(self, script_authorizer):
        session = prawcore.Session(script_authorizer)
        json = {"lang": "ja", "num_comments": 123}
        response = session.request("PATCH", "/api/v1/me/prefs", json=json)
        assert response["lang"] == "ja"
        assert response["num_comments"] == 123

    def test_request__post(self, script_authorizer):
        session = prawcore.Session(script_authorizer)
        data = {
            "kind": "self",
            "sr": "reddit_api_test",
            "text": "Test!",
            "title": "A Test from PRAWCORE.",
        }
        key_count = len(data)
        response = session.request("POST", "/api/submit", data=data)
        assert "a_test_from_prawcore" in response["json"]["data"]["url"]
        assert key_count == len(data)  # Ensure data is untouched

    @pytest.mark.recorder_kwargs(match_requests_on=["uri", "method"])
    def test_request__post__with_files(self, script_authorizer):
        session = prawcore.Session(script_authorizer)
        data = {"upload_type": "header"}
        with open("tests/integration/files/white-square.png", "rb") as fp:
            files = {"file": fp}
            response = session.request(
                "POST",
                "/r/reddit_api_test/api/upload_sr_img",
                data=data,
                files=files,
            )
        assert "img_src" in response

    def test_request__raw_json(self, readonly_authorizer):
        session = prawcore.Session(readonly_authorizer)
        response = session.request(
            "GET",
            "/r/reddit_api_test/comments/45xjdr/want_raw_json_test/",
        )
        assert (
            "WANT_RAW_JSON test: < > &"
            == response[0]["data"]["children"][0]["data"]["title"]
        )

    def test_request__redirect(self, readonly_authorizer):
        session = prawcore.Session(readonly_authorizer)
        with pytest.raises(prawcore.Redirect) as exception_info:
            session.request("GET", "/r/random")
        assert exception_info.value.path.startswith("/r/")

    def test_request__redirect_301(self, readonly_authorizer):
        session = prawcore.Session(readonly_authorizer)
        with pytest.raises(prawcore.Redirect) as exception_info:
            session.request("GET", "t/bird")
        assert exception_info.value.path == "/r/t:bird/"

    def test_request__service_unavailable(self, readonly_authorizer):
        session = prawcore.Session(readonly_authorizer)
        with pytest.raises(prawcore.ServerError) as exception_info:
            session.request("GET", "/")
            session.request("GET", "/")
            session.request("GET", "/")
        assert exception_info.value.response.status_code == 503

    def test_request__too__many_requests__with_retry_headers(self, readonly_authorizer):
        session = prawcore.Session(readonly_authorizer)
        session._requestor._http.headers.update(
            {"User-Agent": "python-requests/2.25.1"}
        )
        with pytest.raises(prawcore.TooManyRequests) as exception_info:
            session.request("GET", "/api/v1/me")
        assert exception_info.value.response.status_code == 429
        assert exception_info.value.response.headers.get("retry-after")
        assert exception_info.value.response.reason == "Too Many Requests"
        assert str(exception_info.value).startswith(
            "received 429 HTTP response. Please wait at least"
        )
        assert exception_info.value.message.startswith("\n<!doctype html>")

    def test_request__too__many_requests__without_retry_headers(self, requestor):
        requestor._http.headers.update({"User-Agent": "python-requests/2.25.1"})
        authorizer = prawcore.ReadOnlyAuthorizer(
            prawcore.TrustedAuthenticator(
                requestor,
                pytest.placeholders.client_id,
                pytest.placeholders.client_secret,
            )
        )
        with pytest.raises(prawcore.exceptions.ResponseException) as exception_info:
            authorizer.refresh()
        assert exception_info.value.response.status_code == 429
        assert not exception_info.value.response.headers.get("retry-after")
        assert exception_info.value.response.reason == "Too Many Requests"
        assert exception_info.value.response.json() == {
            "message": "Too Many Requests",
            "error": 429,
        }

    @pytest.mark.recorder_kwargs(match_requests_on=["uri", "method"])
    def test_request__too_large(self, script_authorizer):
        session = prawcore.Session(script_authorizer)
        data = {"upload_type": "header"}
        with open("tests/integration/files/too_large.jpg", "rb") as fp:
            files = {"file": fp}
            with pytest.raises(prawcore.TooLarge) as exception_info:
                session.request(
                    "POST",
                    "/r/reddit_api_test/api/upload_sr_img",
                    data=data,
                    files=files,
                )
        assert exception_info.value.response.status_code == 413

    def test_request__unavailable_for_legal_reasons(self, readonly_authorizer):
        session = prawcore.Session(readonly_authorizer)
        exception_class = prawcore.UnavailableForLegalReasons
        with pytest.raises(exception_class) as exception_info:
            session.request("GET", "/")
        assert exception_info.value.response.status_code == 451

    def test_request__unsupported_media_type(self, script_authorizer):
        session = prawcore.Session(script_authorizer)
        exception_class = prawcore.SpecialError
        data = {
            "content": "type: submission\naction: upvote",
            "page": "config/automoderator",
        }
        with pytest.raises(exception_class) as exception_info:
            session.request("POST", "r/ttft/api/wiki/edit/", data=data)
        assert exception_info.value.response.status_code == 415

    def test_request__uri_too_long(self, readonly_authorizer):
        session = prawcore.Session(readonly_authorizer)
        path_start = "/api/morechildren?link_id=t3_n7r3uz&children="
        with open("tests/integration/files/comment_ids.txt") as fp:
            ids = fp.read()
        with pytest.raises(prawcore.URITooLong) as exception_info:
            session.request("GET", (path_start + ids)[:9996])
        assert exception_info.value.response.status_code == 414

    def test_request__with_insufficient_scope(self, trusted_authenticator):
        authorizer = prawcore.Authorizer(
            trusted_authenticator, refresh_token=pytest.placeholders.refresh_token
        )
        authorizer.refresh()
        session = prawcore.Session(authorizer)
        with pytest.raises(prawcore.InsufficientScope):
            session.request(
                "GET",
                "/api/v1/me",
            )

    def test_request__with_invalid_access_token(self, untrusted_authenticator):
        authorizer = prawcore.ImplicitAuthorizer(untrusted_authenticator, None, 0, "")
        session = prawcore.Session(authorizer)
        session._authorizer.access_token = "invalid"
        with pytest.raises(prawcore.InvalidToken):
            session.request("get", "/")

    def test_request__with_invalid_access_token__retry(self, readonly_authorizer):
        session = prawcore.Session(readonly_authorizer)
        session._authorizer.access_token += "invalid"
        response = session.request("GET", "/")
        assert isinstance(response, dict)
