"""Shared paging and download machinery for the concrete downloaders."""

from __future__ import annotations

import math
import random
import time
from typing import TYPE_CHECKING, Any

from . import console

if TYPE_CHECKING:
    from collections.abc import Callable, Container, Iterable, Iterator
    from pathlib import Path

    from pixivpy3 import AppPixivAPI
    from pixivpy3.utils import JsonDict

    from .auth import PixivClient
    from .models import IllustInfo

WORKS_PAGE_INTERVAL = 1.5
"""Seconds to wait between pages of one artist's works."""

COUNTDOWN_THRESHOLD = 5.0
"""A sleep at least this long counts itself down instead of looking like a hang."""


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
        """Sleep for `base` seconds plus up to `rand` more, to stay under the rate limit.

        A wait of at least `COUNTDOWN_THRESHOLD` seconds -- the one between
        artists is half a minute -- ticks a `zzz... (n/total)` line once a
        second so the run does not look stuck.
        """
        duration = base + rand * random.random()  # noqa: S311
        if duration < COUNTDOWN_THRESHOLD:
            time.sleep(duration)
            return
        ticks = math.ceil(duration)
        for tick in range(1, ticks + 1):
            console.status(f"[+] zzz... ({tick}/{ticks})")
            time.sleep(min(1.0, duration - (tick - 1)))
        console.clear_line()

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

    def work_count(self, target_id: int) -> int | None:
        """How many illustrations one artist has posted.

        Args:
            target_id: The artist's pixiv user id.

        Returns:
            The count taken from the artist's profile, or None if pixiv did not
            report one.
        """
        count = self.aapi.user_detail(target_id)["profile"].get("total_illusts")
        return None if count is None else int(count)

    def retrieve_works(
        self,
        target_id: int,
        *,
        progress: str | None = None,
        known: Container[int] | None = None,
    ) -> list[IllustInfo]:
        """List the illustrations posted by one artist.

        Args:
            target_id: The artist's pixiv user id.
            progress: Prefix of a transient line reporting how many works have
                been listed so far; no line is printed when it is None.
            known: Ids an earlier run already listed. Paging stops at the first
                work in it: the endpoint answers newest first, so everything
                from there on is what the earlier run saw.

        Returns:
            One entry per illustration, newest first -- every one of them, or
            only the ones posted since `known` was collected.
        """
        works: list[IllustInfo] = []
        suffix = ""
        if progress is not None:
            # The pages themselves carry no count, so the artist's profile is
            # the only place the `n/total` denominator can come from.
            total = self.work_count(target_id)
            suffix = "" if total is None else f"/{total}"
            console.status(f"{progress} - 0{suffix} works")
            self.rand_sleep(WORKS_PAGE_INTERVAL)
        for page in self.paginate(
            self.aapi.user_illusts,
            interval=WORKS_PAGE_INTERVAL,
            user_id=target_id,
            type="illust",
        ):
            for illust in page["illusts"]:
                if known is not None and illust.id in known:
                    return works
                works.append({"id": illust.id, "title": illust.title, "links": self.ext_links(illust)})
            if progress is not None:
                console.status(f"{progress} - {len(works)}{suffix} works")
        return works

    def download(
        self,
        works: Iterable[IllustInfo],
        save_path: Path,
        *,
        total: int | None = None,
        limit: int | None = None,
    ) -> int:
        """Download every page of every work into one directory.

        Files already on disk are left alone, so an interrupted run can simply
        be started again.

        `works` is consumed lazily, so a listing that is still being paged stops
        being paged as soon as `limit` is reached.

        Args:
            works: What `retrieve_works` (or a bookmark listing) collected.
            save_path: Directory to write into; created if missing.
            total: Denominator of the progress counter. Needed when `works` is
                an iterator; a list counts itself.
            limit: Stop after this many works have actually yielded a file. The
                pages of the work that reaches the limit are all downloaded.

        Returns:
            How many works something was actually fetched for; the ones already
            on disk are not counted, so a zero means there was nothing new to
            download.
        """
        if total is None:
            works = list(works)
            total = len(works)
        save_path.mkdir(parents=True, exist_ok=True)
        fetched = 0
        for index, work in enumerate(works, start=1):
            title = work["title"].replace("/", "／")
            new = False
            for link in work["links"]:
                # `123_title_p0.png`: the page suffix is the tail of the original name.
                fname = f"{work['id']}_{title}_{link.split('/')[-1].split('_')[-1]}"
                console.status(f"[+] {console.counter(index, total)}: {title} - {fname}")
                # `AppPixivAPI.download` answers False for a file it left alone.
                new |= bool(self.aapi.download(link, path=str(save_path), fname=fname))
            if not new:
                continue
            fetched += 1
            if limit is not None and fetched >= limit:
                break
        console.clear_line()
        return fetched
