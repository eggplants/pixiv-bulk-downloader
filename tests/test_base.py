from __future__ import annotations

import pytest
from conftest import Attr, FakeAPI, illust, make_client

from pixiv_bulk_downloader import base as base_module
from pixiv_bulk_downloader.base import PixivAPIError, PixivBaseDownloader

# The autouse fixture below replaces the method, so the real one is kept here.
REAL_RAND_SLEEP = PixivBaseDownloader.rand_sleep


@pytest.fixture(autouse=True)
def _no_sleeping(monkeypatch):
    monkeypatch.setattr(PixivBaseDownloader, "rand_sleep", staticmethod(lambda *args, **kwargs: None))


def downloader(pages, save_dir, detail=None):
    api = FakeAPI(pages=pages, detail=detail)
    return PixivBaseDownloader(make_client(api), save_dir), api


def test_ext_links_lists_every_page_of_a_multi_page_work():
    assert PixivBaseDownloader.ext_links(illust(7, pages=3)) == [
        "https://i.pximg.net/7_p0.png",
        "https://i.pximg.net/7_p1.png",
        "https://i.pximg.net/7_p2.png",
    ]


def test_ext_links_falls_back_to_the_single_page_url():
    assert PixivBaseDownloader.ext_links(illust(7)) == ["https://i.pximg.net/7_p0.png"]


def test_ext_links_falls_back_to_the_large_url_without_an_original():
    work = illust(7)
    work["meta_single_page"] = Attr()
    assert PixivBaseDownloader.ext_links(work) == ["https://i.pximg.net/7_large.png"]


def test_paginate_follows_next_url_until_it_runs_out(tmp_path):
    pages = [
        Attr(illusts=[illust(1)], next_url="https://app-api.pixiv.net/v1/user/illusts?user_id=42&offset=30"),
        Attr(illusts=[illust(2)], next_url=None),
    ]
    dl, api = downloader(pages, tmp_path)

    got = list(dl.paginate(api.user_illusts, interval=0, user_id=42, type="illust"))

    assert len(got) == 2
    assert api.calls[0] == ("user_illusts", {"user_id": 42, "type": "illust"})
    assert api.calls[1] == ("user_illusts", {"user_id": "42", "offset": "30"})


def test_paginate_raises_on_an_api_error(tmp_path):
    dl, api = downloader([Attr(error=Attr(message="Rate Limit"))], tmp_path)

    with pytest.raises(PixivAPIError, match="Rate Limit"):
        list(dl.paginate(api.user_illusts, interval=0, user_id=42))


def test_paginate_refreshes_the_token_and_retries_an_expired_page(monkeypatch, tmp_path):
    pages = [
        Attr(error=Attr(message="Error occurred at the OAuth process. invalid_grant")),
        Attr(illusts=[illust(1)], next_url=None),
    ]
    dl, api = downloader(pages, tmp_path)
    refreshed = []
    monkeypatch.setattr(type(dl.client), "refresh", lambda self: refreshed.append(True))

    got = list(dl.paginate(api.user_illusts, interval=0, user_id=42))

    assert refreshed == [True]
    assert len(got) == 1


def test_retrieve_works_flattens_every_page(tmp_path):
    pages = [
        Attr(illusts=[illust(1, "a"), illust(2, "b")], next_url=None),
    ]
    dl, _ = downloader(pages, tmp_path)

    assert dl.retrieve_works(42) == [
        {"id": 1, "title": "a", "links": ["https://i.pximg.net/1_p0.png"]},
        {"id": 2, "title": "b", "links": ["https://i.pximg.net/2_p0.png"]},
    ]


def test_work_count_reads_the_artists_profile(tmp_path):
    dl, _ = downloader([], tmp_path, detail={"profile": {"total_illusts": 12}})

    assert dl.work_count(42) == 12


def test_work_count_is_none_without_a_reported_total(tmp_path):
    dl, _ = downloader([], tmp_path, detail={"profile": {}})

    assert dl.work_count(42) is None


def test_download_names_each_file_after_its_work(tmp_path):
    dl, api = downloader([], tmp_path)
    works = [{"id": 9, "title": "title", "links": ["https://i.pximg.net/9_p0.png", "https://i.pximg.net/9_p1.png"]}]

    dl.download(works, tmp_path / "out")

    assert (tmp_path / "out").is_dir()
    assert api.downloaded == [
        ("https://i.pximg.net/9_p0.png", str(tmp_path / "out"), "9_title_p0.png"),
        ("https://i.pximg.net/9_p1.png", str(tmp_path / "out"), "9_title_p1.png"),
    ]


def test_download_reports_each_file_on_one_line(tmp_path, capsys):
    dl, _ = downloader([], tmp_path)
    works = [{"id": 9, "title": "title", "links": ["https://i.pximg.net/9_p0.png"]}]

    dl.download(works, tmp_path / "out")

    assert "[+]: [1/1]: title - 9_title_p0.png" in capsys.readouterr().out


def works(*ids):
    return [{"id": i, "title": str(i), "links": [f"https://i.pximg.net/{i}_p0.png"]} for i in ids]


def test_download_counts_a_multi_page_work_once(tmp_path):
    dl, api = downloader([], tmp_path)
    api.existing.add("9_title_p0.png")
    work = [{"id": 9, "title": "title", "links": ["https://i.pximg.net/9_p0.png", "https://i.pximg.net/9_p1.png"]}]

    assert dl.download(work, tmp_path / "out") == 1


def test_download_counts_nothing_when_every_file_is_already_there(tmp_path):
    dl, api = downloader([], tmp_path)
    api.existing.add("9_title_p0.png")
    work = [{"id": 9, "title": "title", "links": ["https://i.pximg.net/9_p0.png"]}]

    assert dl.download(work, tmp_path / "out") == 0


def test_download_stops_at_the_limit(tmp_path):
    dl, api = downloader([], tmp_path)

    assert dl.download(works(1, 2, 3), tmp_path / "out", limit=2) == 2
    assert [fname for _, _, fname in api.downloaded] == ["1_1_p0.png", "2_2_p0.png"]


def test_download_spends_the_limit_only_on_works_it_fetched(tmp_path):
    dl, api = downloader([], tmp_path)
    api.existing.update({"1_1_p0.png", "2_2_p0.png"})

    assert dl.download(works(1, 2, 3), tmp_path / "out", limit=1) == 1
    assert [fname for _, _, fname in api.downloaded] == ["1_1_p0.png", "2_2_p0.png", "3_3_p0.png"]


def test_download_leaves_an_iterator_unconsumed_past_the_limit(tmp_path):
    dl, _ = downloader([], tmp_path)
    listing = iter(works(1, 2, 3))

    dl.download(listing, tmp_path / "out", total=3, limit=1)

    assert list(listing) == works(2, 3)


def test_download_counts_a_list_for_its_own_progress_total(tmp_path, capsys):
    dl, _ = downloader([], tmp_path)

    dl.download(works(1, 2), tmp_path / "out")

    assert "[2/2]" in capsys.readouterr().out


def test_download_takes_the_progress_total_of_an_iterator_from_the_caller(tmp_path, capsys):
    dl, _ = downloader([], tmp_path)

    dl.download(iter(works(1)), tmp_path / "out", total=42)

    assert "[01/42]" in capsys.readouterr().out


def test_download_keeps_a_slash_out_of_the_file_name(tmp_path):
    dl, api = downloader([], tmp_path)

    dl.download([{"id": 9, "title": "a/b", "links": ["https://i.pximg.net/9_p0.png"]}], tmp_path / "out")

    assert api.downloaded[0][2] == "9_a／b_p0.png"


def test_rand_sleep_counts_a_long_wait_down(capsys, monkeypatch):
    monkeypatch.setattr(base_module.random, "random", lambda: 0.0)
    slept = []
    monkeypatch.setattr(base_module.time, "sleep", slept.append)

    REAL_RAND_SLEEP(30.0, 0.0)

    assert slept == [1.0] * 30
    out = capsys.readouterr().out
    assert "[+]: zzz... (1/30)" in out
    assert "[+]: zzz... (30/30)" in out


def test_rand_sleep_stays_quiet_for_a_short_wait(capsys, monkeypatch):
    monkeypatch.setattr(base_module.random, "random", lambda: 0.0)
    slept = []
    monkeypatch.setattr(base_module.time, "sleep", slept.append)

    REAL_RAND_SLEEP(1.5, 0.0)

    assert slept == [1.5]
    assert "zzz" not in capsys.readouterr().out


def test_retrieve_works_stops_at_a_work_it_already_knows(tmp_path):
    pages = [
        Attr(illusts=[illust(3, "c"), illust(2, "b")], next_url="https://app-api.pixiv.net/v1/user/illusts?offset=30"),
        Attr(illusts=[illust(1, "a")], next_url=None),
    ]
    dl, api = downloader(pages, tmp_path)

    assert dl.retrieve_works(42, known={2, 1}) == [{"id": 3, "title": "c", "links": ["https://i.pximg.net/3_p0.png"]}]
    # The second page was never asked for.
    assert len(api.pages) == 1


def test_retrieve_works_walks_the_whole_listing_without_a_known_work(tmp_path):
    pages = [Attr(illusts=[illust(2, "b"), illust(1, "a")], next_url=None)]
    dl, _ = downloader(pages, tmp_path)

    assert [work["id"] for work in dl.retrieve_works(42, known={9})] == [2, 1]
