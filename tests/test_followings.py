from __future__ import annotations

import pytest
from conftest import Attr, FakeAPI, illust, make_client

from pixiv_bulk_downloader.base import PixivBaseDownloader
from pixiv_bulk_downloader.followings import PixivFollowingsDownloader


@pytest.fixture(autouse=True)
def _no_sleeping(monkeypatch):
    monkeypatch.setattr(PixivBaseDownloader, "rand_sleep", staticmethod(lambda *args, **kwargs: None))


def artist(id_, name, account):
    return Attr(user=Attr(id=id_, name=name, account=account))


@pytest.fixture
def downloader(tmp_path):
    api = FakeAPI(
        pages=[
            Attr(user_previews=[artist(7, "one", "one_acc")], next_url=None),
            Attr(illusts=[illust(1, "a")], next_url=None),
        ],
        detail={"profile": {"total_follow_users": 1, "total_illusts": 3, "total_illust_bookmarks_public": 0}},
    )
    return PixivFollowingsDownloader(make_client(api), tmp_path), api


def test_retrieve_following_collects_each_artists_works(downloader):
    dl, _ = downloader

    assert list(dl.retrieve_following(1)) == [
        {
            "id": 7,
            "name": "one",
            "account": "one_acc",
            "illusts": [{"id": 1, "title": "a", "links": ["https://i.pximg.net/1_p0.png"]}],
        },
    ]


def test_retrieve_following_skips_a_page_without_artists(tmp_path, capsys):
    api = FakeAPI(pages=[Attr(user_previews=None, next_url=None)], detail={"profile": {"total_follow_users": 0}})
    dl = PixivFollowingsDownloader(make_client(api), tmp_path)

    assert list(dl.retrieve_following(0)) == []
    assert "empty" in capsys.readouterr().err


def test_download_all_gives_each_artist_their_own_directory(downloader, tmp_path):
    dl, api = downloader

    dl.download_all()

    assert api.downloaded == [
        ("https://i.pximg.net/1_p0.png", str(tmp_path / "following" / "7_one_one_acc"), "1_a_p0.png"),
    ]


class OrderedAPI(FakeAPI):
    """Records listing and downloading in the order they happen."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.order = []

    def user_illusts(self, **kwargs):
        self.order.append(("list", kwargs["user_id"]))
        return super().user_illusts(**kwargs)

    def download(self, url, path=None, fname=None, **kwargs):
        self.order.append(("download", fname))
        return super().download(url, path=path, fname=fname, **kwargs)


def test_download_all_downloads_before_listing_the_next_artist(tmp_path):
    api = OrderedAPI(
        pages=[
            Attr(user_previews=[artist(7, "one", "one_acc"), artist(8, "two", "two_acc")], next_url=None),
            Attr(illusts=[illust(1, "a")], next_url=None),
            Attr(illusts=[illust(2, "b")], next_url=None),
        ],
        detail={"profile": {"total_follow_users": 2}},
    )
    dl = PixivFollowingsDownloader(make_client(api), tmp_path)

    dl.download_all()

    assert api.order == [("list", 7), ("download", "1_a_p0.png"), ("list", 8), ("download", "2_b_p0.png")]


def test_retrieve_works_reports_progress_against_the_artists_work_count(downloader, capsys):
    dl, _ = downloader

    list(dl.retrieve_following(1))

    assert "1/3 works" in capsys.readouterr().out


def test_retrieve_works_reports_a_bare_count_without_a_work_total(tmp_path, capsys):
    api = FakeAPI(
        pages=[
            Attr(user_previews=[artist(7, "one", "one_acc")], next_url=None),
            Attr(illusts=[illust(1, "a")], next_url=None),
        ],
        detail={"profile": {"total_follow_users": 1}},
    )
    dl = PixivFollowingsDownloader(make_client(api), tmp_path)

    list(dl.retrieve_following(1))

    assert "1 works" in capsys.readouterr().out
