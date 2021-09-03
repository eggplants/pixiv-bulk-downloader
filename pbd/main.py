#!/usr/bin/env python

import json
import os
import sys
from typing import Optional, Tuple

import stdiomask
from gppt import selenium as s
from pixivpy3 import AppPixivAPI
from pixivpy3.utils import JsonDict

from .bookmarks import BookmarksPixivDownloader
from .followings import FollowingsPixivDownloader
from .types import LoginCred, LoginFailed

SAVE_DIR = os.getenv("SAVE_DIR",
                     os.path.join(os.path.expanduser("~"), 'pbd'))
'''client.json
{
  'pixiv_id' : '<change this>',
  'password' : '<change this>'
}
'''


def get_refresh_token(pixiv_id: str, pixiv_pass: str) -> str:
    gpt = s.GetPixivToken(headless=True, user=pixiv_id, pass_=pixiv_pass)
    res = gpt.login()
    return res["refresh_token"]


def _auth(cnt: int,
          auth_json_path: str = 'client.json') -> Tuple[AppPixivAPI, JsonDict]:
    aapi: AppPixivAPI = AppPixivAPI()
    login_cred: Optional[LoginCred] = None
    if os.path.exists('client.json'):
        cred_data = json.load(open(auth_json_path, 'r'))
        login_cred = (None
                      if set(cred_data.keys()) != {'pixiv_id', 'password'}
                      else cred_data)

    if login_cred is not None and cnt == 0:
        ref = get_refresh_token(login_cred['pixiv_id'], login_cred['password'])
        print('\x1b[?25l[+]: Login...')
        login_info = aapi.auth(refresh_token=ref)
    elif login_cred is None or (login_cred is not None and cnt != 0):
        print('[+]: ID is mail address, userid, account name.')
        stdin_login = (stdiomask.getpass(prompt='[?]: ID: '),
                       stdiomask.getpass(prompt='[?]: PW: '))
        print('\x1b[?25l[+]: Login...', end='\r')
        ref = get_refresh_token(stdin_login[0], stdin_login[1])
        login_info = aapi.auth(refresh_token=ref)
        print('\033[K[+]: Login...OK!')
    else:
        raise LoginFailed

    return (aapi, login_info)


def auth() -> Tuple[AppPixivAPI, JsonDict]:
    cnt = 0
    while cnt < 3:
        try:
            aapi, login_info = _auth(cnt)
        except (ValueError, UnboundLocalError):
            print('\x1b[?25h[!]: Failed to login. Check your ID or PW.')
        else:
            return aapi, login_info
        cnt += 1
    else:
        print('[!]: The number of login attempts has been exceeded.')
        raise LoginFailed


def getch() -> str:
    c = stdiomask.getch()
    print()
    return c


def _main(aapi: AppPixivAPI, login_info: JsonDict) -> None:
    f = FollowingsPixivDownloader(aapi, login_info, SAVE_DIR)
    b = BookmarksPixivDownloader(aapi, login_info, SAVE_DIR)
    my_info = aapi.user_detail(aapi.user_id)
    total_following_len = my_info["profile"]["total_follow_users"]
    total_bookmark_len = my_info["profile"]["total_illust_bookmarks_public"]
    if '-y' in sys.argv:
        f.get_all_following_works()
        print('\033[K[+]: Finish!')
        b.get_all_bookmarked_works()
        print('\033[K[+]: Finish!')
    else:
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


def main() -> None:
    try:
        aapi, login_info = auth()
        _main(aapi, login_info)
    # except (KeyError, LoginFailed):
    #     print('\n[!]: Request limit seem to be exceeded. '
    #           'Try again later.')
    # except KeyboardInterrupt:
    #     print('\n[!]: SIGINT')
    finally:
        print("\x1b[?25h", end='')


if __name__ == '__main__':
    main()
    print("\x1b[?25h", end='')
