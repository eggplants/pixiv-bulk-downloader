"""Download every work posted by the artists the logged-in account follows."""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import console
from .base import PixivBaseDownloader

if TYPE_CHECKING:
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
        """Fetch the works of every followed artist, then download them."""
        console.info("Fetching information of works of following artists...")
        artists = self.retrieve_following()
        console.info("Downloading works of following artists...")
        total = len(artists)
        for index, artist in enumerate(artists, start=1):
            dirname = f"{artist['id']}_{artist['name']}_{artist['account']}".replace("/", "／")
            console.info(f"[Artist]{console.counter(index, total)}: {dirname}")
            self.download(artist["illusts"], self.save_dir / "following" / dirname)
            console.drop_line()

    def retrieve_following(self) -> list[ArtistInfo]:
        """List every followed artist together with all of their illustrations.

        Returns:
            One entry per followed artist.
        """
        total = self.aapi.user_detail(self.client.user_id)["profile"]["total_follow_users"]
        artists: list[ArtistInfo] = []
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
                console.status(f"[+]: {console.counter(len(artists) + 1, total)}: {user.name} (id: {user.id})")
                artists.append(
                    {
                        "id": user.id,
                        "name": user.name,
                        "account": user.account,
                        "illusts": self.retrieve_works(user.id),
                    },
                )
                self.rand_sleep(FOLLOWING_INTERVAL)
        return artists
