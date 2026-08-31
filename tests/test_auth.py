from __future__ import annotations

from conftest import FakeAPI, make_client, token

import pixiv_bulk_downloader.auth as auth_module
from pixiv_bulk_downloader.auth import DEFAULT_PROFILE, PixivClient, login


def test_client_hands_the_token_to_the_api(client, api):
    assert api.auth == ("access", "refresh")
    assert api.user_id == 42
    assert client.user_id == 42


def _never_called(*args, **kwargs):
    msg = "refresh should not have been called"
    raise AssertionError(msg)


def test_ensure_fresh_leaves_a_live_token_alone(monkeypatch, client, api):
    monkeypatch.setattr(auth_module.gppt, "refresh", _never_called)
    client.ensure_fresh()
    assert api.auth == ("access", "refresh")


def test_ensure_fresh_reauthenticates_an_expired_token(monkeypatch, api):
    client = make_client(api, expires_in=-1)
    fresh = token()
    fresh.access_token = "new-access"
    monkeypatch.setattr(auth_module.gppt, "refresh", lambda refresh_token: fresh)

    client.ensure_fresh()

    assert client.token is fresh
    assert api.auth == ("new-access", "refresh")


def test_login_passes_the_options_through_to_gppt(monkeypatch):
    seen = {}

    def fake_get_token(profile, **kwargs):
        seen["profile"] = profile
        seen.update(kwargs)
        return token()

    monkeypatch.setattr(auth_module.gppt, "get_token", fake_get_token)
    monkeypatch.setattr(auth_module, "AppPixivAPI", FakeAPI)

    client = login("other", method="oauth", headless=False, force=True)

    assert isinstance(client, PixivClient)
    assert client.profile == "other"
    assert seen["profile"] == "other"
    assert (seen["method"], seen["headless"], seen["force"]) == ("oauth", False, True)


def test_login_defaults_to_the_default_profile(monkeypatch):
    monkeypatch.setattr(auth_module.gppt, "get_token", lambda profile, **kwargs: token())
    monkeypatch.setattr(auth_module, "AppPixivAPI", FakeAPI)
    assert login().profile == DEFAULT_PROFILE
