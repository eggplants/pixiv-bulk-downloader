from __future__ import annotations

import pytest

from pixiv_bulk_downloader.cache import WorkCache


def works(*ids):
    return [{"id": i, "title": str(i), "links": [f"https://i.pximg.net/{i}_p0.png"]} for i in ids]


@pytest.fixture
def cache(tmp_path):
    with WorkCache(tmp_path / "sub" / "cache.sqlite3") as cache:
        yield cache


def test_an_artist_nobody_listed_yet_has_no_listing(cache):
    assert cache.works(7) is None


def test_a_saved_listing_comes_back_in_order(cache):
    cache.save(7, works(3, 2, 1))

    assert cache.works(7) == works(3, 2, 1)


def test_an_artist_who_posted_nothing_is_not_an_unlisted_one(cache):
    cache.save(7, [])

    assert cache.works(7) == []


def test_saving_again_replaces_the_whole_listing(cache):
    cache.save(7, works(2, 1))
    cache.save(7, works(3, 2, 1))

    assert cache.works(7) == works(3, 2, 1)


def test_a_listing_that_names_a_work_twice_keeps_the_first_of_them(cache):
    cache.save(7, [*works(2), {"id": 2, "title": "renamed", "links": []}, *works(1)])

    assert cache.works(7) == works(2, 1)


def test_each_artist_keeps_their_own_listing(cache):
    cache.save(7, works(1))
    cache.save(8, works(2))

    assert cache.works(7) == works(1)
    assert cache.works(8) == works(2)


def test_the_database_outlives_the_connection(tmp_path):
    path = tmp_path / "cache.sqlite3"
    with WorkCache(path) as cache:
        cache.save(7, works(1))

    assert WorkCache(path).works(7) == works(1)


def test_closing_a_cache_nobody_opened_is_fine(tmp_path):
    WorkCache(tmp_path / "cache.sqlite3").close()

    assert not (tmp_path / "cache.sqlite3").exists()


def test_a_reopened_cache_connects_again(tmp_path):
    cache = WorkCache(tmp_path / "cache.sqlite3")
    cache.save(7, works(1))
    cache.close()

    assert cache.works(7) == works(1)


def test_a_save_that_blows_up_leaves_the_old_listing_alone(cache):
    cache.save(7, works(2, 1))

    # `links` that will not serialize: the rows are written in one transaction,
    # so the listing must not end up half replaced.
    with pytest.raises(TypeError):
        cache.save(7, [{"id": 3, "title": "c", "links": object()}, *works(2, 1)])
    assert cache.works(7) == works(2, 1)
