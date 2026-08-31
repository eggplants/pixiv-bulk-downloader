"""Download every work the logged-in account has bookmarked publicly."""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import console
from .base import PixivBaseDownloader

if TYPE_CHECKING:
    from collections.abc import Iterator

    from .models import IllustInfo

BOOKMARKS_PAGE_INTERVAL = 0.5
"""Seconds to wait between pages of the bookmark listing."""


class PixivBookmarksDownloader(PixivBaseDownloader):
    """Saves bookmarked works into `<save_dir>/bookmarks`."""

    def download_all(self, limit: int | None = None) -> None:
        """Download each bookmarked work as soon as it has been listed.

        Args:
            limit: Stop once this many works have actually been downloaded.
                Works already on disk do not count, so running with a limit
                again picks up where the last run stopped. None downloads every
                bookmark.
        """
        console.info("Downloading bookmarked works...")
        fetched = self.download(
            self.retrieve_bookmarks(),
            self.save_dir / "bookmarks",
            total=self.bookmark_count(),
            limit=limit,
        )
        if limit is not None and fetched >= limit:
            console.info(f"Downloaded {fetched} works, stopping at the limit.")

    def bookmark_count(self) -> int:
        """How many works the logged-in account has bookmarked publicly.

        Returns:
            The bookmark count, used for the progress counters.
        """
        return self.aapi.user_detail(self.client.user_id)["profile"]["total_illust_bookmarks_public"]

    def retrieve_bookmarks(self) -> Iterator[IllustInfo]:
        """Yield every publicly bookmarked illustration.

        One work is yielded at a time so the caller can start downloading right
        away, and so that a caller who stops early leaves the rest of the
        listing unpaged.

        Yields:
            One entry per bookmarked illustration, newest bookmark first.
        """
        for page in self.paginate(
            self.aapi.user_bookmarks_illust,
            interval=BOOKMARKS_PAGE_INTERVAL,
            user_id=self.client.user_id,
        ):
            for illust in page["illusts"]:
                yield {"id": illust.id, "title": illust.title, "links": self.ext_links(illust)}
