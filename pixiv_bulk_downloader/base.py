"""Shared paging and download machinery for the concrete downloaders."""

from __future__ import annotations

import random
import time
from typing import TYPE_CHECKING, Any

from . import console

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from pathlib import Path

    from pixivpy3 import AppPixivAPI
    from pixivpy3.utils import JsonDict

    from .auth import PixivClient
    from .models import IllustInfo

WORKS_PAGE_INTERVAL = 1.5
"""Seconds to wait between pages of one artist's works."""


class PixivAPIError(RuntimeError):
    """Raised when the pixiv API answers with an error body."""


class PixivBaseDownloader:
    """Fetches work metadata page by page and writes the images to disk."""

    def __init__(self, client: PixivClient, save_dir: Path) -> None:
        """Store the authenticated client and the directory to download into."""
        self.client = client
        self.save_dir = save_dir

    @property
    def aapi(self) -> AppPixivAPI:
        """The underlying pixiv API client."""
        return self.client.aapi

    @staticmethod
    def rand_sleep(base: float = 0.1, rand: float = 2.5) -> None:
        """Sleep for `base` seconds plus up to `rand` more, to stay under the rate limit."""
        time.sleep(base + rand * random.random())  # noqa: S311

    @staticmethod
    def ext_links(illust: JsonDict) -> list[str]:
        """Collect the original-size URL of every page of one work.

        Args:
            illust: An `illust` object from the pixiv API.

        Returns:
            One URL per page; single-page works give a one-element list.
        """
        links: list[str] = [page.image_urls.original for page in illust.meta_pages]
        return links or [illust.meta_single_page.get("original_image_url", illust.image_urls.large)]

    def paginate(
        self,
        fetch: Callable[..., JsonDict],
        *,
        interval: float,
        **params: Any,  # noqa: ANN401
    ) -> Iterator[JsonDict]:
        """Walk a paginated pixiv endpoint, yielding one response body per page.

        The query string of each `next_url` is fed straight back into `fetch`,
        which is why every endpoint used here takes its own paging parameters
        by keyword.

        Args:
            fetch: The `AppPixivAPI` method to call.
            interval: Seconds to wait between pages.
            **params: Parameters for the first call.

        Yields:
            The decoded body of each page.

        Raises:
            PixivAPIError: If a page comes back as an error other than an
                expired token.
        """
        next_qs: dict[str, Any] | None = params
        while next_qs is not None:
            self.client.ensure_fresh()
            page = fetch(**next_qs)
            if "error" in page:
                message = str(page["error"].get("message") or page["error"])
                if "invalid_grant" not in message:
                    raise PixivAPIError(message)
                # The access token lapsed mid-run: a fresh one retries this page.
                self.client.refresh()
                continue
            yield page
            next_qs = self.aapi.parse_qs(page.get("next_url"))
            self.rand_sleep(interval)

    def retrieve_works(self, target_id: int) -> list[IllustInfo]:
        """List every illustration posted by one artist.

        Args:
            target_id: The artist's pixiv user id.

        Returns:
            One entry per illustration.
        """
        return [
            {"id": illust.id, "title": illust.title, "links": self.ext_links(illust)}
            for page in self.paginate(
                self.aapi.user_illusts,
                interval=WORKS_PAGE_INTERVAL,
                user_id=target_id,
                type="illust",
            )
            for illust in page["illusts"]
        ]

    def download(self, works: list[IllustInfo], save_path: Path) -> None:
        """Download every page of every work into one directory.

        Files already on disk are left alone, so an interrupted run can simply
        be started again.

        Args:
            works: What `retrieve_works` (or a bookmark listing) collected.
            save_path: Directory to write into; created if missing.
        """
        save_path.mkdir(parents=True, exist_ok=True)
        total = len(works)
        for index, work in enumerate(works, start=1):
            title = work["title"].replace("/", "／")
            console.info(f"{console.counter(index, total)}: {title} (id: {work['id']})")
            for link in work["links"]:
                # `123_title_p0.png`: the page suffix is the tail of the original name.
                fname = f"{work['id']}_{title}_{link.split('/')[-1].split('_')[-1]}"
                console.status(fname)
                self.aapi.download(link, path=str(save_path), fname=fname)
            console.drop_line()
