from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import cast

import pytest
from gppt import Token
from pixivpy3 import AppPixivAPI

from pixiv_bulk_downloader.auth import PixivClient


class FakeAPI:
    """Stands in for `AppPixivAPI`, recording what the downloaders ask of it."""

    def __init__(self, pages=None, detail=None, existing=()):
        self.pages = list(pages or [])
        self.detail = detail or {"profile": {"total_follow_users": 0, "total_illust_bookmarks_public": 0}}
        self.auth = None
        self.user_id = 0
        self.downloaded = []
        self.calls = []
        # File names the real `AppPixivAPI.download` would leave alone, and so answer False for.
        self.existing = set(existing)

    def set_auth(self, access_token, refresh_token=None):
        self.auth = (access_token, refresh_token)

    def user_detail(self, user_id, **kwargs):
        self.calls.append(("user_detail", user_id))
        return self.detail

    def _next_page(self, name, kwargs):
        self.calls.append((name, kwargs))
        return self.pages.pop(0)

    def user_illusts(self, **kwargs):
        return self._next_page("user_illusts", kwargs)

    def user_bookmarks_illust(self, **kwargs):
        return self._next_page("user_bookmarks_illust", kwargs)

    def user_following(self, **kwargs):
        return self._next_page("user_following", kwargs)

    @staticmethod
    def parse_qs(next_url):
        return AppPixivAPI.parse_qs(next_url)

    def download(self, url, path=None, fname=None, **kwargs):
        self.downloaded.append((url, path, fname))
        return fname not in self.existing


class Attr(dict):
    """A dict whose keys are also attributes, like pixivpy's `JsonDict`."""

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc


def illust(id_=1, title="work", *, pages=0):
    """Build an `illust` object the way the pixiv API returns one."""
    return Attr(
        id=id_,
        title=title,
        meta_pages=[Attr(image_urls=Attr(original=f"https://i.pximg.net/{id_}_p{n}.png")) for n in range(pages)],
        meta_single_page=Attr(original_image_url=f"https://i.pximg.net/{id_}_p0.png"),
        image_urls=Attr(large=f"https://i.pximg.net/{id_}_large.png"),
    )


def token(*, expires_in=3600, refresh_token="refresh"):
    expires_at = datetime.now(tz=UTC) + timedelta(seconds=expires_in)
    return Token(
        access_token="access",
        refresh_token=refresh_token,
        expires_in=expires_in,
        expires_at=expires_at.isoformat(),
        user_id="42",
        user_name="eggplant",
        user_account="eggplants",
    )


def make_client(api, **kwargs):
    """Wrap a `FakeAPI` in a client; the cast is the price of a stand-in."""
    return PixivClient(token(**kwargs), aapi=cast("AppPixivAPI", api))


@pytest.fixture
def api():
    return FakeAPI()


@pytest.fixture
def client(api):
    return make_client(api)
