from __future__ import annotations

import random
import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

    from gppt import LoginInfo
    from pixivpy3 import AppPixivAPI
    from pixivpy3.utils import JsonDict

    from .pixiv_types import IllustInfo


class PixivBaseDownloader:
    def __init__(
        self, aapi: AppPixivAPI, login_info: LoginInfo, save_dir: Path
    ) -> None:
        self.aapi = aapi
        self.login_info = login_info
        self.save_dir = save_dir

    @staticmethod
    def rand_sleep(base: float = 0.1, rand: float = 2.5) -> None:
        time.sleep(base + rand * random.random())  # noqa: S311

    @staticmethod
    def ext_links(illust: JsonDict) -> list[str] | str:
        links: list[str] = [page.image_urls.original for page in illust.meta_pages]
        link: str = illust.meta_single_page.get(
            "original_image_url",
            illust.image_urls.large,
        )

        return links if links != [] else link

    def retrieve_works(self, target_id: int) -> list[IllustInfo]:
        urls: list[IllustInfo] = []
        next_qs: dict[str, Any] | None = {}
        while next_qs is not None:
            if next_qs == {}:
                res_json = self.aapi.user_illusts(target_id, type="illust")
            else:
                res_json = self.aapi.user_illusts(**next_qs)
            if "error" in res_json and "invalid_grant" in res_json["error"]["message"]:
                self.aapi.auth()
                continue
            for illust in res_json["illusts"]:
                urls.append(  # noqa: PERF401
                    {
                        "id": illust.id,
                        "title": illust.title,
                        "link": self.ext_links(illust),
                    },
                )
            next_qs = self.aapi.parse_qs(res_json["next_url"])
            self.rand_sleep(1.5)
        return urls

    def download(self, data: list[IllustInfo], save_path: Path) -> None:
        save_path.mkdir(parents=True, exist_ok=True)
        data_len = len(data)
        d_width = len(str(data_len))
        for idx, image_data in enumerate(data):
            title, id_ = image_data["title"].replace("/", "／"), image_data["id"]
            links = image_data["link"]
            print(
                f"\033[K[%0{d_width}d/%0{d_width}d]: %s (id: %d)"
                % (idx + 1, data_len, title, id_),
            )
            self.__download(links, title, id_, save_path)

            print("\033[K\033[A\033[K", end="", flush=True)

    def __download(
        self,
        links: str | list[str],
        title: str,
        id_: int,
        save_path: Path,
    ) -> None:
        if isinstance(links, list):
            for link in links:
                basename_: str = link.split("/")[-1]
                fname = "{}_{}_{}".format(id_, title, basename_.split("_")[-1])
                print("\033[K" + fname, end="\r")
                self.aapi.download(link, path=str(save_path), fname=fname)
        elif isinstance(links, str):
            link = links
            basename_ = link.split("/")[-1]
            fname = "{}_{}_{}".format(id_, title, basename_.split("_")[-1])
            print("\033[K" + fname, end="\r")
            self.aapi.download(link, path=str(save_path), fname=fname)
