"""Test for prawcore.Sessions module."""
import logging
from json import dumps

import pytest
from betamax import Betamax
from mock import patch
from testfixtures import LogCapture

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
    def client_authorizer(self):
        authenticator = prawcore.TrustedAuthenticator(
            self.requestor,
            pytest.placeholders.client_id,
            pytest.placeholders.client_secret,
        )
        authorizer = prawcore.Authorizer(
            authenticator, refresh_token=pytest.placeholders.refresh_token
        )
        authorizer.refresh()
        return authorizer

    def readonly_authorizer(self, refresh=True, requestor=None):
        authenticator = prawcore.TrustedAuthenticator(
            requestor or self.requestor,
            pytest.placeholders.client_id,
            pytest.placeholders.client_secret,
        )
        authorizer = prawcore.ReadOnlyAuthorizer(authenticator)
        if refresh:
            authorizer.refresh()
        return authorizer

    def script_authorizer(self):
        authenticator = prawcore.TrustedAuthenticator(
            self.requestor,
            pytest.placeholders.client_id,
            pytest.placeholders.client_secret,
        )
        authorizer = prawcore.ScriptAuthorizer(
            authenticator,
            pytest.placeholders.username,
            pytest.placeholders.password,
            two_factor_callback,
        )
        authorizer.refresh()
        return authorizer

    def test_request__accepted(self):
        with self.use_cassette("Session_request__accepted"):
            session = prawcore.Session(self.script_authorizer())
            with LogCapture(level=logging.DEBUG) as log_capture:
                session.request("POST", "api/read_all_messages")
            log_capture.check_present(("prawcore", "DEBUG", "Response: 202 (2 bytes)"))

    def test_request__get(self):
        with self.use_cassette("Session_request__get"):
            session = prawcore.Session(self.readonly_authorizer())
            params = {"limit": 100}
            response = session.request("GET", "/", params=params)
        assert isinstance(response, dict)
        assert len(params) == 1
        assert response["kind"] == "Listing"

    def test_request__patch(self):
        with self.use_cassette(
            "Session_request__patch",
            match_requests_on=["method", "uri", "body"],
        ):
            session = prawcore.Session(self.script_authorizer())
            json = {"lang": "ja", "num_comments": 123}
            response = session.request("PATCH", "/api/v1/me/prefs", json=json)
            assert response["lang"] == "ja"
            assert response["num_comments"] == 123

    def test_request__post(self):
        with self.use_cassette("Session_request__post"):
            session = prawcore.Session(self.script_authorizer())
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

    def test_request__post__with_files(self):
        with self.use_cassette(
            "Session_request__post__with_files",
            match_requests_on=["uri", "method"],
        ):
            session = prawcore.Session(self.script_authorizer())
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

    def test_request__raw_json(self):
        with self.use_cassette("Session_request__raw_json"):
            session = prawcore.Session(self.readonly_authorizer())
            response = session.request(
                "GET",
                "/r/reddit_api_test/comments/45xjdr/want_raw_json_test/",
            )
        assert (
            "WANT_RAW_JSON test: < > &"
            == response[0]["data"]["children"][0]["data"]["title"]
        )

    @patch("time.sleep", return_value=None)
    def test_request__bad_gateway(self, _):
        with self.use_cassette("Session_request__bad_gateway"):
            session = prawcore.Session(self.readonly_authorizer())
            with pytest.raises(prawcore.ServerError) as exception_info:
                session.request("GET", "/")
            assert exception_info.value.response.status_code == 502

    def test_request__bad_json(self):
        with self.use_cassette("Session_request__bad_json"):
            session = prawcore.Session(self.script_authorizer())
            with pytest.raises(prawcore.BadJSON) as exception_info:
                session.request("GET", "/")
            assert len(exception_info.value.response.content) == 92

    def test_request__bad_request(self):
        with self.use_cassette("Session_request__bad_request"):
            session = prawcore.Session(self.script_authorizer())
            with pytest.raises(prawcore.BadRequest) as exception_info:
                session.request(
                    "PUT",
                    "/api/v1/me/friends/spez",
                    data='{"note": "prawcore"}',
                )
            assert "reason" in exception_info.value.response.json()

    @patch("time.sleep", return_value=None)
    def test_request__cloudflare_connection_timed_out(self, _):
        with self.use_cassette("Session_request__cloudflare_connection_timed_out"):
            session = prawcore.Session(self.readonly_authorizer())
            with pytest.raises(prawcore.ServerError) as exception_info:
                session.request("GET", "/")
                session.request("GET", "/")
                session.request("GET", "/")
            assert exception_info.value.response.status_code == 522

    @patch("time.sleep", return_value=None)
    def test_request__cloudflare_unknown_error(self, _):
        with self.use_cassette("Session_request__cloudflare_unknown_error"):
            session = prawcore.Session(self.readonly_authorizer())
            with pytest.raises(prawcore.ServerError) as exception_info:
                session.request("GET", "/")
                session.request("GET", "/")
                session.request("GET", "/")
            assert exception_info.value.response.status_code == 520

    def test_request__conflict(self):
        with self.use_cassette("Session_request__conflict"):
            session = prawcore.Session(self.script_authorizer())
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

    def test_request__created(self):
        with self.use_cassette("Session_request__created"):
            session = prawcore.Session(self.script_authorizer())
            response = session.request("PUT", "/api/v1/me/friends/spez", data="{}")
            assert "name" in response

    def test_request__forbidden(self):
        with self.use_cassette("Session_request__forbidden"):
            session = prawcore.Session(self.script_authorizer())
            with pytest.raises(prawcore.Forbidden):
                session.request(
                    "GET",
                    "/user/spez/gilded/given",
                )

    @patch("time.sleep", return_value=None)
    def test_request__gateway_timeout(self, _):
        with self.use_cassette("Session_request__gateway_timeout"):
            session = prawcore.Session(self.readonly_authorizer())
            with pytest.raises(prawcore.ServerError) as exception_info:
                session.request("GET", "/")
            assert exception_info.value.response.status_code == 504

    @patch("time.sleep", return_value=None)
    def test_request__internal_server_error(self, _):
        with self.use_cassette("Session_request__internal_server_error"):
            session = prawcore.Session(self.readonly_authorizer())
            with pytest.raises(prawcore.ServerError) as exception_info:
                session.request("GET", "/")
            assert exception_info.value.response.status_code == 500

    def test_request__no_content(self):
        with self.use_cassette("Session_request__no_content"):
            session = prawcore.Session(self.script_authorizer())
            response = session.request("DELETE", "/api/v1/me/friends/spez")
            assert response is None

    def test_request__not_found(self):
        with self.use_cassette("Session_request__not_found"):
            session = prawcore.Session(self.script_authorizer())
            with pytest.raises(prawcore.NotFound):
                session.request(
                    "GET",
                    "/r/reddit_api_test/wiki/invalid",
                )

    def test_request__okay_with_0_byte_content(self):
        with self.use_cassette("Session_request__okay_with_0_byte_content"):
            session = prawcore.Session(self.script_authorizer())
            data = {"model": dumps({"name": "redditdev"})}
            path = f"/api/multi/user/{pytest.placeholders.username}/m/praw_x5g968f66a/r/redditdev"
            response = session.request("DELETE", path, data=data)
            assert response == ""

    def test_request__redirect(self):
        with self.use_cassette("Session_request__redirect"):
            session = prawcore.Session(self.readonly_authorizer())
            with pytest.raises(prawcore.Redirect) as exception_info:
                session.request("GET", "/r/random")
            assert exception_info.value.path.startswith("/r/")

    def test_request__redirect_301(self):
        with self.use_cassette("Session_request__redirect_301"):
            session = prawcore.Session(self.readonly_authorizer())
            with pytest.raises(prawcore.Redirect) as exception_info:
                session.request("GET", "t/bird")
            assert exception_info.value.path == "/r/t:bird/"

    @patch("time.sleep", return_value=None)
    def test_request__service_unavailable(self, _):
        with self.use_cassette("Session_request__service_unavailable"):
            session = prawcore.Session(self.readonly_authorizer())
            with pytest.raises(prawcore.ServerError) as exception_info:
                session.request("GET", "/")
                session.request("GET", "/")
                session.request("GET", "/")
            assert exception_info.value.response.status_code == 503

    def test_request__too_large(self):
        with self.use_cassette(
            "Session_request__too_large", match_requests_on=["uri", "method"]
        ):
            session = prawcore.Session(self.script_authorizer())
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

    def test_request__too__many_requests__with_retry_headers(self):
        with self.use_cassette(
            "Session_request__too__many_requests__with_retry_headers"
        ):
            session = prawcore.Session(
                self.readonly_authorizer(requestor=self.requestor)
            )
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

    def test_request__too__many_requests__without_retry_headers(self):
        requestor = prawcore.Requestor("python-requests/2.25.1")

        with Betamax(requestor).use_cassette(
            "Session_request__too__many_requests__without_retry_headers"
        ):
            with pytest.raises(prawcore.exceptions.ResponseException) as exception_info:
                prawcore.Session(self.readonly_authorizer(requestor=requestor))
            assert exception_info.value.response.status_code == 429
            assert not exception_info.value.response.headers.get("retry-after")
            assert exception_info.value.response.reason == "Too Many Requests"
            assert exception_info.value.response.json() == {
                "message": "Too Many Requests",
                "error": 429,
            }

    def test_request__unavailable_for_legal_reasons(self):
        with self.use_cassette("Session_request__unavailable_for_legal_reasons"):
            session = prawcore.Session(self.readonly_authorizer())
            exception_class = prawcore.UnavailableForLegalReasons
            with pytest.raises(exception_class) as exception_info:
                session.request("GET", "/")
            assert exception_info.value.response.status_code == 451

    def test_request__unsupported_media_type(self):
        with self.use_cassette("Session_request__unsupported_media_type"):
            session = prawcore.Session(self.script_authorizer())
            exception_class = prawcore.SpecialError
            data = {
                "content": "type: submission\naction: upvote",
                "page": "config/automoderator",
            }
            with pytest.raises(exception_class) as exception_info:
                session.request("POST", "r/ttft/api/wiki/edit/", data=data)
            assert exception_info.value.response.status_code == 415

    def test_request__uri_too_long(self):
        with self.use_cassette("Session_request__uri_too_long"):
            session = prawcore.Session(self.readonly_authorizer())
            path_start = "/api/morechildren?link_id=t3_n7r3uz&children="
            with open("tests/integration/files/comment_ids.txt") as fp:
                ids = fp.read()
            with pytest.raises(prawcore.URITooLong) as exception_info:
                session.request("GET", (path_start + ids)[:9996])
            assert exception_info.value.response.status_code == 414

    def test_request__with_insufficient_scope(self):
        with self.use_cassette("Session_request__with_insufficient_scope"):
            session = prawcore.Session(self.client_authorizer())
            with pytest.raises(prawcore.InsufficientScope):
                session.request(
                    "GET",
                    "/api/v1/me",
                )

    def test_request__with_invalid_access_token(self):
        authenticator = prawcore.UntrustedAuthenticator(
            self.requestor, pytest.placeholders.client_id
        )
        authorizer = prawcore.ImplicitAuthorizer(authenticator, None, 0, "")
        session = prawcore.Session(authorizer)

        with self.use_cassette("Session_request__with_invalid_access_token"):
            session._authorizer.access_token = "invalid"
            with pytest.raises(prawcore.InvalidToken):
                session.request("get", "/")

    @patch("time.sleep", return_value=None)
    def test_request__with_invalid_access_token__retry(self, _):
        with self.use_cassette("Session_request__with_invalid_access_token__retry"):
            session = prawcore.Session(self.readonly_authorizer())
            session._authorizer.access_token += "invalid"
            response = session.request("GET", "/")
        assert isinstance(response, dict)
