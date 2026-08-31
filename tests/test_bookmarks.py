from __future__ import annotations

import pytest
from conftest import Attr, FakeAPI, illust, make_client

from pixiv_bulk_downloader.base import PixivBaseDownloader
from pixiv_bulk_downloader.bookmarks import PixivBookmarksDownloader


@pytest.fixture(autouse=True)
def _no_sleeping(monkeypatch):
    monkeypatch.setattr(PixivBaseDownloader, "rand_sleep", staticmethod(lambda *args, **kwargs: None))


@pytest.fixture
def downloader(tmp_path):
    api = FakeAPI(
        pages=[
            Attr(illusts=[illust(1, "a")], next_url="https://app-api.pixiv.net/v1/user/bookmarks/illust?user_id=42"),
            Attr(illusts=[illust(2, "b")], next_url=None),
        ],
        detail={"profile": {"total_illust_bookmarks_public": 2, "total_follow_users": 0}},
    )
    return PixivBookmarksDownloader(make_client(api), tmp_path), api


def test_retrieve_bookmarks_walks_every_page(downloader):
    dl, api = downloader

    assert dl.retrieve_bookmarks() == [
        {"id": 1, "title": "a", "links": ["https://i.pximg.net/1_p0.png"]},
        {"id": 2, "title": "b", "links": ["https://i.pximg.net/2_p0.png"]},
    ]
    assert api.calls[0] == ("user_detail", 42)


def test_download_all_saves_under_a_bookmarks_directory(downloader, tmp_path):
    dl, api = downloader

    dl.download_all()

    assert {path for _, path, _ in api.downloaded} == {str(tmp_path / "bookmarks")}
    assert [name for _, _, name in api.downloaded] == ["1_a_p0.png", "2_b_p0.png"]
