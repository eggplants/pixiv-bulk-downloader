import os
import random
import time
from typing import Dict, List, Optional, Union

from pixivpy3 import AppPixivAPI
from pixivpy3.utils import JsonDict

from .pixiv_types import IllustInfo


class PixivBaseDownloader:
    def __init__(self, aapi: AppPixivAPI, login_info: JsonDict, save_dir: str):
        self.aapi = aapi
        self.login_info = login_info
        self.save_dir = save_dir

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
            if 'error' in res_json \
                    and 'invalid_grant' in res_json['error']['message']:
                self.aapi.auth()
                continue
            for illust in res_json['illusts']:
                urls.append(
                    {
                        'id': illust.id,
                        'title': illust.title,
                        'link': self.ext_links(illust)
                    }
                )
            next = self.aapi.parse_qs(res_json['next_url'])
            self.rand_sleep(1.5)
        else:
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
            links = image_data['link']
            print(f'\033[K[%0{d_width}d/%0{d_width}d]: %s (id: %d)'
                  % (idx + 1, data_len, title, id_))
            self.__download(links, title, id_, save_path)

            print('\033[K\033[A\033[K', end='', flush=True)

    def __download(self, links: Union[str, List[str]],
                   title: str, id_: int, save_path: str) -> None:
        if type(links) is list:
            for link in links:
                basename_: str = link.split('/')[-1]
                fname = '{}_{}_{}'.format(
                    id_, title, basename_.split('_')[-1])
                print('\033[K' + fname, end="\r")
                self.aapi.download(link, path=save_path, fname=fname)
        elif type(links) is str:
            link = links
            basename_ = link.split('/')[-1]
            fname = '{}_{}_{}'.format(id_, title, basename_.split('_')[-1])
            print('\033[K' + fname, end="\r")
            self.aapi.download(link, path=save_path, fname=fname)
