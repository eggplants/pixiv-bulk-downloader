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
    dl, _ = downloader

    assert list(dl.retrieve_bookmarks()) == [
        {"id": 1, "title": "a", "links": ["https://i.pximg.net/1_p0.png"]},
        {"id": 2, "title": "b", "links": ["https://i.pximg.net/2_p0.png"]},
    ]


def test_retrieve_bookmarks_pages_only_as_far_as_it_is_read(downloader):
    dl, api = downloader

    next(dl.retrieve_bookmarks())

    assert len(api.pages) == 1


def test_download_all_saves_under_a_bookmarks_directory(downloader, tmp_path):
    dl, api = downloader

    dl.download_all()

    assert {path for _, path, _ in api.downloaded} == {str(tmp_path / "bookmarks")}
    assert [name for _, _, name in api.downloaded] == ["1_a_p0.png", "2_b_p0.png"]
    assert api.calls[0] == ("user_detail", 42)


def test_download_all_stops_once_the_limit_of_works_has_been_downloaded(downloader):
    dl, api = downloader

    dl.download_all(1)

    assert [name for _, _, name in api.downloaded] == ["1_a_p0.png"]
    # The second page of the listing was never asked for.
    assert len(api.pages) == 1


def test_download_all_does_not_count_a_work_that_is_already_on_disk(downloader):
    dl, api = downloader
    api.existing.add("1_a_p0.png")

    dl.download_all(1)

    # The first work had nothing new, so the limit is only spent on the second.
    assert [name for _, _, name in api.downloaded] == ["1_a_p0.png", "2_b_p0.png"]


def test_download_all_says_it_stopped_at_the_limit(downloader, capsys):
    dl, _ = downloader

    dl.download_all(1)

    assert "stopping at the limit" in capsys.readouterr().out


def test_download_all_without_a_limit_says_nothing_about_one(downloader, capsys):
    dl, _ = downloader

    dl.download_all()

    assert "limit" not in capsys.readouterr().out
