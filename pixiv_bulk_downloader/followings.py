from __future__ import annotations

import os
from typing import Any

from pixivpy3.utils import JsonDict

from .base import PixivBaseDownloader
from .pixiv_types import UserInfo


class PixivFollowingsDownloader(PixivBaseDownloader):
    def retrieve_following(self) -> list[UserInfo]:
        users: list[UserInfo] = []
        next_qs: dict[str, Any] | None = {}
        my_info = self.aapi.user_detail(self.aapi.user_id)
        total = my_info["profile"]["total_follow_users"]
        while next_qs is not None:
            if "user_id" not in next_qs:
                res_json: JsonDict = self.aapi.user_following(
                    self.login_info["response"]["user"]["id"]
                )
            else:
                res_json = self.aapi.user_following(**next_qs)

            next_qs = self.aapi.parse_qs(res_json.next_url)
            now_retrieved_len = len(users)
            users.extend(
                self.extract_artist_info(
                    res_json.user_previews, total, now_retrieved_len
                )
            )
            self.rand_sleep(1.5)

        return users

    def extract_artist_info(
        self, user_previews: Any, following_total: int, retrieved: int
    ) -> list[Any]:
        users: list[Any] = []
        d_width = len(str(following_total))
        if user_previews is None:
            print("\n[!]Warning: artist info seems to be empty.")
            return users
        for idx, user in enumerate(user_previews):
            user_info: JsonDict = user.user
            print(
                f"\033[K[+]: [%0{d_width}d/%0{d_width}d]: %s (id: %d)"
                % (retrieved + idx + 1, following_total, user_info.name, user_info.id),
                end="\r",
                flush=True,
            )
            users.append(
                {
                    "id": user_info.id,
                    "name": user_info.name,
                    "account": user_info.account,
                    "illusts": self.retrieve_works(user_info.id),
                }
            )
            self.rand_sleep(1.5)
        else:
            return users

    def get_all_following_works(self) -> None:
        print("[+]: Fetching information of works of following artists...")
        following_data = self.retrieve_following()
        print("[+]: Downloading works of following artists...")
        following_len = len(following_data)
        d_width = len(str(following_len))
        for idx, author_data in enumerate(following_data):
            dirname = "{}_{}_{}".format(
                author_data["id"], author_data["name"], author_data["account"]
            ).replace("/", "／")
            print(
                f"\033[K[Artist][%0{d_width}d/%0{d_width}d]: %s"
                % (idx + 1, following_len, dirname)
            )
            self.download(
                author_data["illusts"],
                os.path.join(self.save_dir, "following", dirname),
            )
            print("\033[K\033[A\033[K", end="", flush=True)
