#!/usr/bin/env python

import json
import os
import random
import sys
import time
from typing import Any, Dict, List, Optional, Tuple, TypedDict, Union

from gppt import selenium as s
from pixivpy3 import AppPixivAPI  # type: ignore
from pixivpy3.utils import JsonDict  # type: ignore
from stdiomask import getch, getpass

'''client.json
{
  'pixiv_id' : '<change this>',
  'password' : '<change this>'
}
'''


class LoginFailed(Exception):
    pass


class LoginCred(TypedDict):
    pixiv_id: str
    password: str


class IllustInfo(TypedDict):
    id: int
    title: str
    link: Union[str, List[str]]


class UserInfo(TypedDict):
    id: int
    name: str
    account: str
    illusts: List[IllustInfo]


def get_refresh_token(pixiv_id: str, pixiv_pass: str) -> str:
    gpt = s.GetPixivToken(headless=True, user=pixiv_id, pass_=pixiv_pass)
    res = gpt.login()
    return res["refresh_token"]


def rand_sleep(base: float = 0.1, rand: float = 2.5) -> None:
    time.sleep(base + rand * random.random())


def _auth(cnt: int) -> Tuple[AppPixivAPI, JsonDict]:
    login_cred: Optional[LoginCred] = (
        json.load(open('client.json', 'r'))
        if os.path.exists('client.json') else None)
    aapi: AppPixivAPI = AppPixivAPI()

    if (login_cred is None) and cnt < 1:
        print('[+]: ID is mail address, userid, account name.')
        stdin_login = (getpass(prompt='[?]: ID: '),
                       getpass(prompt='[?]: PW: '))
        print('\x1b[?25l[+]: Login...', end='\r')
        ref = get_refresh_token(stdin_login[0], stdin_login[1])
        login_info = aapi.auth(refresh_token=ref)
        print('\033[K[+]: Login...=>OK!')
    elif login_cred is not None:
        ref = get_refresh_token(login_cred['pixiv_id'], login_cred['password'])
        print('\x1b[?25l[+]: Login...')
        aapi.auth(refresh_token=ref)

    return (aapi, login_info)


def auth() -> Tuple[AppPixivAPI, JsonDict]:
    cnt = 0
    while cnt < 3:
        try:
            return _auth(cnt)
        except ValueError:
            print('\x1b[?25h[!]: Failed to login. Check your ID or PW.')
        cnt += 1
    else:
        print('[!]: The number of login attempts has been exceeded.')
        raise LoginFailed


def ext_links(illust: JsonDict) -> Union[List[str], str]:
    links: List[str] = [
        page.image_urls.original for page in illust.meta_pages]
    link: str = illust.meta_single_page.get(
        'original_image_url', illust.image_urls.large)

    return (links if links != [] else link)


def retrieve_bookmarks(
        aapi: AppPixivAPI, login_info: JsonDict) -> List[IllustInfo]:
    urls: List[IllustInfo] = []
    next: Optional[Union[Dict[str, Any], str]] = ""
    target_id = login_info.response.user.id
    total = aapi.user_detail(aapi.user_id)[
        "profile"]["total_illust_bookmarks_public"]
    d_width = len(str(total))
    urls_len = 0
    while next is not None:
        if next == "":
            res_json: JsonDict = aapi.user_bookmarks_illust(target_id)
        else:
            res_json = aapi.user_bookmarks_illust(**next)
        for idx, illust in enumerate(res_json['illusts']):
            print(f'\033[K[+]: [%0{d_width}d/%0{d_width}d]: %s (id: %d)'
                  % (urls_len+idx+1, total, illust.title, illust.id),
                  end='\r', flush=True)
            urls.append(
                {
                    'id': illust.id,
                    'title': illust.title,
                    'link': ext_links(illust)}
            )
        next = aapi.parse_qs(res_json['next_url'])
        urls_len = len(urls)
        rand_sleep(0.5)
    else:
        return urls


def retrieve_works(aapi: AppPixivAPI, id_: int) -> List[IllustInfo]:
    urls: List[IllustInfo] = []
    next: Optional[Union[Dict[str, Any], str]] = ""
    target_id = id_
    while next is not None:
        if next == "":
            res_json = aapi.user_illusts(target_id, type='illust')
        else:
            res_json = aapi.user_illusts(**next)
        for illust in res_json['illusts']:
            urls.append({
                'id': illust.id,
                'title': illust.title,
                'link': ext_links(illust)}
            )
        next = aapi.parse_qs(res_json['next_url'])
        rand_sleep(1.5)

    return urls


def retrieve_following(aapi: AppPixivAPI, login_info: JsonDict)\
        -> List[UserInfo]:
    users: List[UserInfo] = []
    next_qs = ""
    total = aapi.user_detail(aapi.user_id)["profile"]["total_follow_users"]
    while next_qs is not None:
        if next_qs == "":
            res_json: JsonDict = aapi.user_following(
                login_info.response.user.id)
        else:
            res_json = aapi.user_following(**next_qs)

        next_qs = aapi.parse_qs(res_json.next_url)
        now_retrieved_len = len(users)
        users.extend(extract_artist_info(
            aapi, res_json.user_previews,
            total, now_retrieved_len))
        rand_sleep(10.5)

    return users


def extract_artist_info(aapi: AppPixivAPI, user_previews: Any,
                        following_total: int, retrieved: int) -> List[Any]:
    users: List[Any] = []
    d_width = len(str(following_total))
    if user_previews is None:
        print('\n[!]Warning: artist info seems to be empty.')
        return users
    for idx, user in enumerate(user_previews):
        user_info: JsonDict = user.user
        print(f'\033[K[+]: [%0{d_width}d/%0{d_width}d]: %s (id: %d)'
              % (retrieved+idx+1, following_total,
                 user_info.name, user_info.id),
              end="\r", flush=True)
        users.append({
            "id": user_info.id,
            "name": user_info.name,
            "account": user_info.account,
            "illusts": retrieve_works(aapi, user_info.id)})
        rand_sleep(1.5)
    else:
        return users


SAVE_DIR = os.path.join(os.path.expanduser("~"), 'pbd')


def download(
        aapi: AppPixivAPI, data: List[IllustInfo],
        save_dir: str = SAVE_DIR) -> None:
    os.makedirs(save_dir, exist_ok=True)
    data_len = len(data)
    d_width = len(str(data_len))
    for idx, image_data in enumerate(data):
        title, id_ = image_data['title'].replace('/', '／'), image_data['id']
        link = image_data['link']
        print(f'\033[K[%0{d_width}d/%0{d_width}d]: %s (id: %d)'
              % (idx + 1, data_len, title, id_))
        if type(link) is list:
            for _ in link:
                basename_: str = _.split('/')[-1]
                fname = '{}_{}_{}'.format(id_, title, basename_.split('_')[-1])
                print('\033[K' + fname, end="\r")
                aapi.download(_, path=save_dir, fname=fname)
        else:
            basename_ = link.split('/')[-1]  # type: ignore
            fname = '{}_{}_{}'.format(id_, title, basename_.split('_')[-1])
            print('\033[K' + fname, end="\r")
            aapi.download(link, path=save_dir, fname=fname)

        print('\033[K\033[A\033[K', end='', flush=True)


def get_all_following_works(aapi: AppPixivAPI, login_info: JsonDict) -> None:
    print("[+]: Fetching infomation of works of following artists...")
    following_data = retrieve_following(aapi, login_info)
    print("[+]: Downloading works of following artists...")
    following_len = len(following_data)
    d_width = len(str(following_len))
    for idx, author_data in enumerate(following_data):
        dirname = '{}_{}_{}'.format(
            author_data['id'], author_data['name'],
            author_data['account']).replace('/', '／')
        print(f'\033[K[Artist][%0{d_width}d/%0{d_width}d]: %s'
              % (idx + 1, following_len, dirname))
        download(aapi, author_data['illusts'],
                 os.path.join(SAVE_DIR, 'following', dirname))
        print('\033[K\033[A\033[K', end='', flush=True)


def get_all_bookmarked_works(aapi: AppPixivAPI, login_info: JsonDict) -> None:
    print('\n[+]: Fetching infomation of bookmarked works...')
    bookmarked_data = retrieve_bookmarks(aapi, login_info)
    print('\n[+]: Downloading bookmarked works...')
    download(aapi, bookmarked_data, os.path.join(SAVE_DIR, 'bookmarks'))


def _main(aapi: AppPixivAPI, login_info: JsonDict) -> None:
    my_info = aapi.user_detail(aapi.user_id)
    total_following_len = my_info["profile"]["total_follow_users"]
    total_bookmark_len = my_info["profile"]["total_illust_bookmarks_public"]
    if '-y' in sys.argv:
        get_all_following_works(aapi, login_info)
        print('\033[K[+]: Finish!')
        get_all_bookmarked_works(aapi, login_info)
        print('\033[K[+]: Finish!')
    else:
        print('[?]: Download all works of following? '
              '({} artists) (n/y): '.format(total_following_len),
              end='', flush=True)
        if getch() == 'y':
            get_all_following_works(aapi, login_info)
            print('\033[K[+]: Finish!')
        print('[?]: Download all bookmarked? '
              '({} works) (n/y): '.format(total_bookmark_len),
              end='',  flush=True)
        if getch() == 'y':
            get_all_bookmarked_works(aapi, login_info)
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
