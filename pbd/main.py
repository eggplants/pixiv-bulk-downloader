#!/usr/bin/env python

import os
import sys

import stdiomask
from pixivpy3.aapi import AppPixivAPI

from .auth import PixivAuth
from .bookmarks import PixivBookmarksDownloader
from .followings import PixivFollowingsDownloader
from .pixiv_types import LoginFailed

SAVE_DIR = os.getenv("SAVE_DIR",
                     os.path.join(os.path.expanduser("~"), 'pbd'))
'''client.json
{
  'pixiv_id' : '<change this>',
  'password' : '<change this>'
}
'''


def interact(aapi: AppPixivAPI,
             f: PixivFollowingsDownloader,
             b: PixivBookmarksDownloader) -> None:
    def getch() -> str:
        c = stdiomask.getch()
        print()
        return c
    my_info = aapi.user_detail(aapi.user_id)
    total_following_len = my_info["profile"]["total_follow_users"]
    total_bookmark_len = my_info["profile"]["total_illust_bookmarks_public"]
    print('[?]: Download all works of following? '
          '({} artists) (n/y): '.format(total_following_len),
          flush=True, end="")
    if getch() == 'y':
        f.get_all_following_works()
        print('\033[K[+]: Finish!')
    print('[?]: Download all bookmarked? '
          '({} works) (n/y): '.format(total_bookmark_len),
          flush=True, end="")
    if getch() == 'y':
        b.get_all_bookmarked_works()
        print('\033[K[+]: Finish!')


def _main() -> None:
    aapi, login_info = PixivAuth().auth()
    f = PixivFollowingsDownloader(aapi, login_info, SAVE_DIR)
    b = PixivBookmarksDownloader(aapi, login_info, SAVE_DIR)
    if '-y' in sys.argv:
        f.get_all_following_works()
        print('\033[K[+]: Finish!')
        b.get_all_bookmarked_works()
        print('\033[K[+]: Finish!')
    else:
        interact(aapi, f, b)


def main() -> None:
    try:
        _main()
    except (KeyError, LoginFailed):
        print('\n[!]: Request limit seem to be exceeded. '
              'Try again later.')
    except KeyboardInterrupt:
        print('\n[!]: SIGINT')
    finally:
        print("\x1b[?25h", end='')


if __name__ == '__main__':
    main()
