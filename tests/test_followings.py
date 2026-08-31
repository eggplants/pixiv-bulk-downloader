from __future__ import annotations

import pytest
from conftest import Attr, FakeAPI, illust, make_client

from pixiv_bulk_downloader.base import PixivAPIError, PixivBaseDownloader
from pixiv_bulk_downloader.cache import CACHE_FILENAME
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


def three_artists(tmp_path, existing=()):
    """A following list of three artists with one work each."""
    api = FakeAPI(
        pages=[
            Attr(
                user_previews=[artist(7, "one", "one_acc"), artist(8, "two", "two_acc"), artist(9, "three", "3_acc")],
                next_url=None,
            ),
            Attr(illusts=[illust(1, "a")], next_url=None),
            Attr(illusts=[illust(2, "b")], next_url=None),
            Attr(illusts=[illust(3, "c")], next_url=None),
        ],
        detail={"profile": {"total_follow_users": 3}},
        existing=existing,
    )
    return PixivFollowingsDownloader(make_client(api), tmp_path), api


def test_download_all_without_a_limit_walks_the_whole_following_list(tmp_path):
    dl, api = three_artists(tmp_path)

    dl.download_all()

    assert [fname for _, _, fname in api.downloaded] == ["1_a_p0.png", "2_b_p0.png", "3_c_p0.png"]


def test_download_all_stops_once_the_limit_of_artists_has_been_downloaded(tmp_path):
    dl, api = three_artists(tmp_path)

    dl.download_all(2)

    assert [fname for _, _, fname in api.downloaded] == ["1_a_p0.png", "2_b_p0.png"]
    # The third artist's works were never even listed.
    assert len(api.pages) == 1


def test_download_all_does_not_count_an_artist_whose_works_are_all_on_disk(tmp_path):
    dl, api = three_artists(tmp_path, existing=["1_a_p0.png", "2_b_p0.png"])

    dl.download_all(1)

    # The first two artists had nothing new, so the limit is only spent on the third.
    assert [fname for _, _, fname in api.downloaded] == ["1_a_p0.png", "2_b_p0.png", "3_c_p0.png"]
    assert api.pages == []


def test_download_all_says_it_stopped_at_the_limit(tmp_path, capsys):
    dl, _ = three_artists(tmp_path)

    dl.download_all(1)

    assert "stopping at the limit" in capsys.readouterr().out


def test_the_first_run_lists_everything_and_writes_it_down(downloader, tmp_path):
    dl, _ = downloader

    dl.download_all()

    assert dl.cache.works(7) == [{"id": 1, "title": "a", "links": ["https://i.pximg.net/1_p0.png"]}]


def test_the_cache_lands_in_the_save_directory(downloader, tmp_path):
    dl, _ = downloader

    dl.download_all()

    assert (tmp_path / CACHE_FILENAME).is_file()


def cached_downloader(tmp_path, pages, cached):
    """A downloader whose artist 7 has already been listed down to `cached`."""
    api = FakeAPI(
        pages=[Attr(user_previews=[artist(7, "one", "one_acc")], next_url=None), *pages],
        detail={"profile": {"total_follow_users": 1}},
    )
    dl = PixivFollowingsDownloader(make_client(api), tmp_path)
    dl.cache.save(7, cached)
    return dl, api


def work(id_, title):
    return {"id": id_, "title": title, "links": [f"https://i.pximg.net/{id_}_p0.png"]}


def test_a_later_run_stops_listing_at_the_newest_cached_work(tmp_path):
    dl, api = cached_downloader(
        tmp_path,
        pages=[
            Attr(
                illusts=[illust(3, "c"), illust(2, "b")],
                next_url="https://app-api.pixiv.net/v1/user/illusts?user_id=7&offset=30",
            ),
            Attr(illusts=[illust(1, "a")], next_url=None),
        ],
        cached=[work(2, "b"), work(1, "a")],
    )

    dl.download_all()

    # The new work first, then what the cache held; the second page was never fetched.
    assert [fname for _, _, fname in api.downloaded] == ["3_c_p0.png", "2_b_p0.png", "1_a_p0.png"]
    assert len(api.pages) == 1


def test_a_later_run_writes_the_new_works_in_front_of_the_cached_ones(tmp_path):
    dl, _ = cached_downloader(
        tmp_path,
        pages=[Attr(illusts=[illust(3, "c"), illust(2, "b")], next_url=None)],
        cached=[work(2, "b"), work(1, "a")],
    )

    dl.download_all()

    assert dl.cache.works(7) == [work(3, "c"), work(2, "b"), work(1, "a")]


def test_a_later_run_with_nothing_new_asks_for_one_page_only(tmp_path):
    dl, api = cached_downloader(
        tmp_path,
        pages=[
            Attr(illusts=[illust(2, "b")], next_url="https://app-api.pixiv.net/v1/user/illusts?user_id=7&offset=30")
        ],
        cached=[work(2, "b"), work(1, "a")],
    )

    dl.download_all()

    assert [fname for _, _, fname in api.downloaded] == ["2_b_p0.png", "1_a_p0.png"]
    assert api.pages == []


def test_an_interrupted_listing_leaves_the_cache_as_it_was(tmp_path):
    dl, _ = cached_downloader(
        tmp_path,
        pages=[Attr(error=Attr(message="Rate Limit"))],
        cached=[work(2, "b"), work(1, "a")],
    )

    with pytest.raises(PixivAPIError, match="Rate Limit"):
        dl.download_all()
    assert dl.cache.works(7) == [work(2, "b"), work(1, "a")]


def test_an_artist_the_cache_has_never_seen_is_listed_in_full(tmp_path):
    dl, _ = cached_downloader(
        tmp_path,
        pages=[Attr(illusts=[illust(9, "z")], next_url=None)],
        cached=[],
    )
    dl.cache.save(8, [work(1, "a")])

    dl.download_all()

    assert dl.cache.works(7) == [work(9, "z")]
