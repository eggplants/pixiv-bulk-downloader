from __future__ import annotations

import pixiv_bulk_downloader


def test_version_is_available():
    assert pixiv_bulk_downloader.__version__


def test_public_names_are_importable():
    for name in pixiv_bulk_downloader.__all__:
        assert hasattr(pixiv_bulk_downloader, name)
