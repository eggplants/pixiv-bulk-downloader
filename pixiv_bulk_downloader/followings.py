"""Download every work posted by the artists the logged-in account follows."""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import console
from .base import PixivBaseDownloader

if TYPE_CHECKING:
    from collections.abc import Iterator

    from .models import ArtistInfo

FOLLOWING_INTERVAL = 30.0
"""Seconds to wait between artists.

Walking a whole following list means one request per artist plus one per page
of their works, which trips pixiv's rate limit long before it finishes unless
the crawl is this slow.
"""


class PixivFollowingsDownloader(PixivBaseDownloader):
    """Saves each followed artist's works into `<save_dir>/following/<id>_<name>_<account>`."""

    def download_all(self) -> None:
        """Download each followed artist's works as soon as that artist has been listed."""
        console.info("Downloading works of following artists...")
        total = self.following_count()
        for index, artist in enumerate(self.retrieve_following(total), start=1):
            dirname = f"{artist['id']}_{artist['name']}_{artist['account']}".replace("/", "／")
            console.info(f"[Artist]{console.counter(index, total)}: {dirname}")
            self.download(artist["illusts"], self.save_dir / "following" / dirname)
            console.drop_line()

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
                    "illusts": self.retrieve_works(user.id, progress=progress),
                }
                self.rand_sleep(FOLLOWING_INTERVAL)
