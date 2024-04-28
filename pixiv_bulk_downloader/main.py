from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pwinput  # type: ignore[import-untyped]
from gppt import PixivAuth

from .bookmarks import PixivBookmarksDownloader
from .followings import PixivFollowingsDownloader
from .pixiv_types import LoginFailedError

if TYPE_CHECKING:
    from pixivpy3.aapi import AppPixivAPI

SAVE_DIR = Path(os.getenv("SAVE_DIR", Path.home() / "pbd"))
"""client.json
{
  'pixiv_id' : '<change this>',
  'password' : '<change this>'
}
"""


def interact(
    aapi: AppPixivAPI,
    f: PixivFollowingsDownloader,
    b: PixivBookmarksDownloader,
) -> None:
    def getch() -> str:
        c = pwinput.getch()
        print()
        return str(c)

    my_info = aapi.user_detail(aapi.user_id)
    total_following_len = my_info["profile"]["total_follow_users"]
    total_bookmark_len = my_info["profile"]["total_illust_bookmarks_public"]
    print(
        "[?]: Download all works of following? "
        f"({total_following_len} artists) (n/y): ",
        flush=True,
        end="",
    )
    if getch() == "y":
        f.get_all_following_works()
        print("\033[K[+]: Finish!")
    print(
        "[?]: Download all bookmarked? " f"({total_bookmark_len} works) (n/y): ",
        flush=True,
        end="",
    )
    if getch() == "y":
        b.get_all_bookmarked_works()
        print("\033[K[+]: Finish!")


def _main() -> None:
    aapi, login_info = PixivAuth().auth()
    f = PixivFollowingsDownloader(aapi, login_info, SAVE_DIR)
    b = PixivBookmarksDownloader(aapi, login_info, SAVE_DIR)
    if "-y" in sys.argv:
        f.get_all_following_works()
        print("\033[K[+]: Finish!")
        b.get_all_bookmarked_works()
        print("\033[K[+]: Finish!")
    else:
        interact(aapi, f, b)


def main() -> None:
    try:
        _main()
    except (KeyError, LoginFailedError):
        print("\n[!]: Request limit seem to be exceeded. Try again later.")
    except KeyboardInterrupt:
        print("\n[!]: SIGINT")
    finally:
        print("\x1b[?25h", end="")


if __name__ == "__main__":
    main()
