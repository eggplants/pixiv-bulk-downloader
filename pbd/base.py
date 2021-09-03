
import os
import random
import time
from typing import Dict, List, Optional, Union

from gppt import selenium as s
from pixivpy3 import AppPixivAPI
from pixivpy3.utils import JsonDict

from .types import IllustInfo


class BasePixivDownloader:
    def __init__(self, aapi: AppPixivAPI, login_info: JsonDict, save_dir: str):
        self.aapi = aapi
        self.login_info = login_info
        self.save_dir = save_dir

    def refresh(self) -> None:
        if self.aapi.refresh_token is not None:
            res = s.GetPixivToken.refresh(
                refresh_token=self.aapi.refresh_token)
            if self.aapi.refresh_token == res['refresh_token']:
                print("[!]refreshing")
                self.aapi.auth(refresh_token=res["refresh_token"])
                print('[+]refreshed!')

    @staticmethod
    def rand_sleep(base: float = 0.1, rand: float = 2.5) -> None:
        time.sleep(base + rand * random.random())

    @staticmethod
    def ext_links(illust: JsonDict) -> Union[List[str], str]:
        links: List[str] = [
            page.image_urls.original for page in illust.meta_pages]
        link: str = illust.meta_single_page.get(
            'original_image_url', illust.image_urls.large)

        return (links if links != [] else link)

    def retrieve_works(self, target_id: int) -> List[IllustInfo]:
        urls: List[IllustInfo] = []
        next: Optional[Dict[str, str]] = {}
        while next is not None:
            if next == {}:
                res_json = self.aapi.user_illusts(target_id, type='illust')
            else:
                res_json = self.aapi.user_illusts(**next)  # type: ignore

            for illust in res_json['illusts']:
                urls.append({
                    'id': illust.id,
                    'title': illust.title,
                    'link': self.ext_links(illust)}
                )
            next = self.aapi.parse_qs(res_json['next_url'])
            self.rand_sleep(1.5)

        return urls

    def download(
            self, data: List[IllustInfo],
            save_path: str) -> None:
        os.makedirs(save_path, exist_ok=True)
        data_len = len(data)
        d_width = len(str(data_len))
        for idx, image_data in enumerate(data):
            title, id_ = image_data['title'].replace(
                '/', '／'), image_data['id']
            link = image_data['link']
            print(f'\033[K[%0{d_width}d/%0{d_width}d]: %s (id: %d)'
                  % (idx + 1, data_len, title, id_))
            if type(link) is list:
                for _ in link:
                    basename_: str = _.split('/')[-1]
                    fname = '{}_{}_{}'.format(
                        id_, title, basename_.split('_')[-1])
                    print('\033[K' + fname, end="\r")
                    self.aapi.download(_, path=save_path, fname=fname)
            else:
                basename_ = link.split('/')[-1]  # type: ignore
                fname = '{}_{}_{}'.format(id_, title, basename_.split('_')[-1])
                print('\033[K' + fname, end="\r")
                self.aapi.download(link, path=save_path, fname=fname)

            print('\033[K\033[A\033[K', end='', flush=True)
