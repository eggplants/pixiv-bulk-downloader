import os
from typing import List

from pixivpy3.utils import JsonDict

from .base import PixivBaseDownloader
from .pixiv_types import IllustInfo


class PixivBookmarksDownloader(PixivBaseDownloader):
    def get_all_bookmarked_works(self) -> None:
        print("[+]: Fetching infomation of bookmarked works...")
        bookmarked_data = self.retrieve_bookmarks()
        print("\n[+]: Downloading bookmarked works...")
        self.download(bookmarked_data, os.path.join(self.save_dir, "bookmarks"))

    def retrieve_bookmarks(self) -> List[IllustInfo]:
        urls: List[IllustInfo] = []
        next_qs = {}  # type: ignore[var-annotated]
        target_id = self.login_info["response"]["user"]["id"]
        total = self.aapi.user_detail(self.aapi.user_id)["profile"][
            "total_illust_bookmarks_public"
        ]
        d_width = len(str(total))
        urls_len = 0
        while next_qs is not None:
            if "user_id" not in next_qs:
                res_json: JsonDict = self.aapi.user_bookmarks_illust(target_id)
            else:
                res_json = self.aapi.user_bookmarks_illust(**next_qs)
            for idx, illust in enumerate(res_json["illusts"]):
                print(
                    f"\033[K[+]: [%0{d_width}d/%0{d_width}d]: %s (id: %d)"
                    % (urls_len + idx + 1, total, illust.title, illust.id),
                    end="\r",
                    flush=True,
                )
                urls.append(
                    {
                        "id": illust.id,
                        "title": illust.title,
                        "link": self.ext_links(illust),
                    }
                )
            next_qs = self.aapi.parse_qs(res_json["next_url"])  # type: ignore[assignment]
            urls_len = len(urls)
            self.rand_sleep(0.5)
        else:
            return urls
