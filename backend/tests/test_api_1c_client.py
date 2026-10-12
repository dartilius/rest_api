from unittest.mock import Mock

import pytest
import requests
from django.core.management.base import CommandError

from services.api_1c_client import APIClient1C
from services.management.commands.auth_1c import Command as AuthCommand
from services.management.commands.ping_1c import Command as PingCommand


@pytest.fixture
def client(monkeypatch):
    # Avoid sharing the production singleton/session and never access the database.
    instance = object.__new__(APIClient1C)
    instance.base_url = "https://example.test/1c"
    instance.session = Mock()
    user = Mock(
        email="service@example.test",
        token_1c_access="old-access",
        token_1c_refresh="old-refresh",
    )
    monkeypatch.setattr(instance, "_get_service_user", lambda: user)
    return instance, user


def token_response(data):
    response = Mock()
    response.json.return_value = data
    return response


def test_authenticate_saves_both_tokens(client):
    api, user = client
    api.session.post.return_value = token_response(
        {"access": "new-access", "refresh": "new-refresh"}
    )
    assert api.authenticate("password") is True
    api.session.post.assert_called_once_with(
        "https://example.test/1c/auth/jwt/create",
        json={"email": "service@example.test", "password": "password"},
        timeout=10,
    )
    assert user.token_1c_access == "new-access"
    assert user.token_1c_refresh == "new-refresh"
    user.save.assert_called_once_with(
        update_fields=["token_1c_access", "token_1c_refresh"]
    )


@pytest.mark.parametrize("data", [None, [], {}, {"access": "a"},
                                       {"access": 42, "refresh": "r"},
                                       {"access": "a", "refresh": ""}])
def test_invalid_auth_response_keeps_existing_tokens(client, data):
    api, user = client
    api.session.post.return_value = token_response(data)
    assert api.authenticate("password") is False
    assert user.token_1c_access == "old-access"
    assert user.token_1c_refresh == "old-refresh"
    user.save.assert_not_called()


@pytest.mark.parametrize("error", [requests.Timeout(), requests.HTTPError(), ValueError()])
def test_auth_request_errors_do_not_save_tokens(client, error):
    api, user = client
    api.session.post.side_effect = error
    assert api.authenticate("password") is False
    user.save.assert_not_called()


def test_missing_password_does_not_send_request(client):
    api, user = client
    assert api.authenticate("") is False
    api.session.post.assert_not_called()
    user.save.assert_not_called()


@pytest.mark.parametrize("rotate", [False, True])
def test_refresh_saves_access_and_preserves_or_rotates_refresh(client, rotate):
    api, user = client
    data = {"access": "new-access"}
    if rotate:
        data["refresh"] = "new-refresh"
    api.session.post.return_value = token_response(data)
    assert api.refresh_access() is True
    api.session.post.assert_called_once_with(
        "https://example.test/1c/auth/jwt/refresh",
        json={"refresh": "old-refresh"}, timeout=10,
    )
    assert user.token_1c_access == "new-access"
    assert user.token_1c_refresh == ("new-refresh" if rotate else "old-refresh")
    user.save.assert_called_once_with(update_fields=(
        ["token_1c_access", "token_1c_refresh"] if rotate else ["token_1c_access"]
    ))


@pytest.mark.parametrize("data", [{}, {"access": ""}, {"access": "a", "refresh": None}])
def test_invalid_refresh_does_not_overwrite_tokens(client, data):
    api, user = client
    api.session.post.return_value = token_response(data)
    assert api.refresh_access() is False
    user.save.assert_not_called()
    assert user.token_1c_access == "old-access"
    assert user.token_1c_refresh == "old-refresh"


def test_missing_refresh_does_not_send_request(client):
    api, user = client
    user.token_1c_refresh = None
    assert api.refresh_access() is False
    api.session.post.assert_not_called()


@pytest.mark.parametrize("method", ["get", "post", "patch", "delete"])
def test_403_refreshes_and_retries_original_request_once(client, method):
    api, user = client
    first, second = Mock(status_code=403), Mock(status_code=200)
    calls = []

    def request(*args, **kwargs):
        calls.append((args, {**kwargs, "headers": dict(kwargs["headers"])}))
        return first if len(calls) == 1 else second

    api.session.request.side_effect = request
    api.session.post.return_value = token_response({"access": "new-access"})
    payload = {"name": "test"}
    args = ("/resource", payload) if method in ("post", "patch") else ("/resource",)
    original_headers = {"authorization": "ignored", "X-Test": "value"}
    result = getattr(api, method)(*args, headers=original_headers, timeout=7, params={"q": 1})
    assert result is second
    assert len(calls) == 2
    for index, access in enumerate(["old-access", "new-access"]):
        positional, kwargs = calls[index]
        assert positional == (method.upper(), "https://example.test/1c/resource")
        assert kwargs["headers"] == {"Authorization": f"access_token {access}", "X-Test": "value"}
        assert kwargs["timeout"] == 7
        assert kwargs["params"] == {"q": 1}
        if method in ("post", "patch"):
            assert kwargs["json"] == payload
    assert original_headers == {"authorization": "ignored", "X-Test": "value"}
    assert user.token_1c_access == "new-access"


def test_repeated_403_does_not_loop(client):
    api, _ = client
    forbidden = Mock(status_code=403)
    api.session.request.return_value = forbidden
    api.session.post.return_value = token_response({"access": "new-access"})
    assert api.get("resource") is forbidden
    assert api.session.request.call_count == 2
    assert api.session.post.call_count == 1


def test_failed_refresh_returns_original_403(client):
    api, user = client
    forbidden = Mock(status_code=403)
    api.session.request.return_value = forbidden
    api.session.post.side_effect = requests.Timeout()
    assert api.get("/resource") is forbidden
    api.session.request.assert_called_once()
    user.save.assert_not_called()


@pytest.mark.parametrize("status", [200, 401, 500])
def test_other_statuses_do_not_refresh(client, status):
    api, _ = client
    response = Mock(status_code=status)
    api.session.request.return_value = response
    assert api.get("/resource") is response
    api.session.request.assert_called_once()
    api.session.post.assert_not_called()


def test_missing_access_requires_initial_auth(client):
    api, user = client
    user.token_1c_access = None
    with pytest.raises(RuntimeError, match="auth_1c"):
        api.get("/resource")
    api.session.request.assert_not_called()


def test_ping_does_not_require_service_user_or_tokens(client, monkeypatch):
    api, _ = client
    lookup = Mock(side_effect=AssertionError("Must not look up a service user"))
    monkeypatch.setattr(api, "_get_service_user", lookup)
    assert api.ping() is api.session.get.return_value
    api.session.get.assert_called_once_with("https://example.test/1c/ping/open", timeout=10)
    lookup.assert_not_called()


def test_auth_command_requires_password(monkeypatch):
    monkeypatch.delenv("SERVICE_1C_PASSWORD", raising=False)
    with pytest.raises(CommandError, match="SERVICE_1C_PASSWORD"):
        AuthCommand().handle()


def test_ping_command_reports_failure(monkeypatch):
    api = Mock()
    api.ping.side_effect = requests.Timeout()
    monkeypatch.setattr("services.management.commands.ping_1c.api_1c", api)
    with pytest.raises(CommandError, match="недоступен"):
        PingCommand().handle()
