"""Download every work posted by the artists the logged-in account follows."""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import console
from .base import PixivBaseDownloader
from .cache import CACHE_FILENAME, WorkCache

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from .auth import PixivClient
    from .models import ArtistInfo, IllustInfo

FOLLOWING_INTERVAL = 30.0
"""Seconds to wait between artists.

Walking a whole following list means one request per artist plus one per page
of their works, which trips pixiv's rate limit long before it finishes unless
the crawl is this slow.
"""


class PixivFollowingsDownloader(PixivBaseDownloader):
    """Saves each followed artist's works into `<save_dir>/following/<id>_<name>_<account>`."""

    def __init__(self, client: PixivClient, save_dir: Path, cache: WorkCache | None = None) -> None:
        """Store the client, the download directory and the listing cache.

        Args:
            client: The authenticated client.
            save_dir: Directory to download into.
            cache: Where the listings walked so far are kept. Defaults to the
                database in the save directory.
        """
        super().__init__(client, save_dir)
        self.cache = WorkCache(save_dir / CACHE_FILENAME) if cache is None else cache

    def download_all(self, limit: int | None = None) -> None:
        """Download each followed artist's works as soon as that artist has been listed.

        Args:
            limit: Stop once this many artists have actually yielded a file.
                Artists whose works are already all on disk do not count, so
                running with a limit again picks up where the last run stopped.
                None downloads the whole following list.
        """
        console.info("Downloading works of following artists...")
        total = self.following_count()
        fetched_from = 0
        with self.cache:
            for index, artist in enumerate(self.retrieve_following(total), start=1):
                dirname = f"{artist['id']}_{artist['name']}_{artist['account']}".replace("/", "／")
                console.info(f"[Artist]{console.counter(index, total)}: {dirname}")
                fetched = self.download(artist["illusts"], self.save_dir / "following" / dirname)
                console.drop_line()
                if not fetched:
                    continue
                fetched_from += 1
                if limit is not None and fetched_from >= limit:
                    console.info(f"Downloaded from {fetched_from} artists, stopping at the limit.")
                    break

    def following_count(self) -> int:
        """How many artists the logged-in account follows.

        Returns:
            The follow count, used for the progress counters.
        """
        return self.aapi.user_detail(self.client.user_id)["profile"]["total_follow_users"]

    def retrieve_following(self, total: int) -> Iterator[ArtistInfo]:
        """Yield every followed artist together with all of their illustrations.

        One artist is listed at a time so the caller can start downloading
        right away instead of waiting for the whole following list, which takes
        one request per artist plus one per page of their works.

        Args:
            total: How many artists are expected, for the progress counter.

        Yields:
            One entry per followed artist, in the order pixiv lists them.
        """
        count = 0
        for page in self.paginate(
            self.aapi.user_following,
            interval=FOLLOWING_INTERVAL,
            user_id=self.client.user_id,
        ):
            previews = page.get("user_previews")
            if not previews:
                console.warn("Artist info seems to be empty.")
                continue
            for preview in previews:
                user = preview.user
                count += 1
                progress = f"[+]: {console.counter(count, total)}: {user.name} (id: {user.id})"
                console.status(progress)
                yield {
                    "id": user.id,
                    "name": user.name,
                    "account": user.account,
                    "illusts": self.cached_works(user.id, progress=progress),
                }
                self.rand_sleep(FOLLOWING_INTERVAL)

    def cached_works(self, artist_id: int, *, progress: str | None = None) -> list[IllustInfo]:
        """List one artist's works, paging only as far back as the cache reaches.

        A first run walks the whole listing; a later one stops at the newest
        work it already has and puts the fresh works in front of the cached
        ones. The cache is only written once the walk has come that far, so an
        interrupted run leaves the old listing in place rather than a truncated
        one.

        Args:
            artist_id: The artist's pixiv user id.
            progress: Prefix of the transient line `retrieve_works` reports the
                listing progress on.

        Returns:
            Every illustration the artist has posted, newest first.
        """
        cached = self.cache.works(artist_id)
        known = None if cached is None else {work["id"] for work in cached}
        fresh = self.retrieve_works(artist_id, progress=progress, known=known)
        if cached is None:
            self.cache.save(artist_id, fresh)
            return fresh
        if not fresh:
            return cached
        fresh_ids = {work["id"] for work in fresh}
        works = fresh + [work for work in cached if work["id"] not in fresh_ids]
        self.cache.save(artist_id, works)
        return works
