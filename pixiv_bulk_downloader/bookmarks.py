"""Download every work the logged-in account has bookmarked publicly."""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import console
from .base import PixivBaseDownloader

if TYPE_CHECKING:
    from .models import IllustInfo

BOOKMARKS_PAGE_INTERVAL = 0.5
"""Seconds to wait between pages of the bookmark listing."""


class PixivBookmarksDownloader(PixivBaseDownloader):
    """Saves bookmarked works into `<save_dir>/bookmarks`."""

    def download_all(self) -> None:
        """Fetch the bookmark listing, then download everything in it."""
        console.info("Fetching information of bookmarked works...")
        works = self.retrieve_bookmarks()
        console.info("Downloading bookmarked works...")
        self.download(works, self.save_dir / "bookmarks")

    def retrieve_bookmarks(self) -> list[IllustInfo]:
        """List every publicly bookmarked illustration.

        Returns:
            One entry per bookmarked illustration.
        """
        total = self.aapi.user_detail(self.client.user_id)["profile"]["total_illust_bookmarks_public"]
        works: list[IllustInfo] = []
        for page in self.paginate(
            self.aapi.user_bookmarks_illust,
            interval=BOOKMARKS_PAGE_INTERVAL,
            user_id=self.client.user_id,
        ):
            for illust in page["illusts"]:
                console.status(f"[+]: {console.counter(len(works) + 1, total)}: {illust.title} (id: {illust.id})")
                works.append({"id": illust.id, "title": illust.title, "links": self.ext_links(illust)})
        return works
