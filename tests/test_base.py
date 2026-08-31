from __future__ import annotations

import pytest
from conftest import Attr, FakeAPI, illust, make_client

from pixiv_bulk_downloader.base import PixivAPIError, PixivBaseDownloader


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


def test_download_names_each_file_after_its_work(tmp_path):
    dl, api = downloader([], tmp_path)
    works = [{"id": 9, "title": "title", "links": ["https://i.pximg.net/9_p0.png", "https://i.pximg.net/9_p1.png"]}]

    dl.download(works, tmp_path / "out")

    assert (tmp_path / "out").is_dir()
    assert api.downloaded == [
        ("https://i.pximg.net/9_p0.png", str(tmp_path / "out"), "9_title_p0.png"),
        ("https://i.pximg.net/9_p1.png", str(tmp_path / "out"), "9_title_p1.png"),
    ]


def test_download_keeps_a_slash_out_of_the_file_name(tmp_path):
    dl, api = downloader([], tmp_path)

    dl.download([{"id": 9, "title": "a/b", "links": ["https://i.pximg.net/9_p0.png"]}], tmp_path / "out")

    assert api.downloaded[0][2] == "9_a／b_p0.png"
