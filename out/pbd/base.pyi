from .pixiv_types import IllustInfo as IllustInfo
from gppt import LoginInfo as LoginInfo
from pixivpy3 import AppPixivAPI as AppPixivAPI
from pixivpy3.utils import JsonDict as JsonDict
from typing import Any, List, Union

class PixivBaseDownloader:
    aapi: Any
    login_info: Any
    save_dir: Any
    def __init__(self, aapi: AppPixivAPI, login_info: LoginInfo, save_dir: str) -> None: ...
    @staticmethod
    def rand_sleep(base: float = ..., rand: float = ...) -> None: ...
    @staticmethod
    def ext_links(illust: JsonDict) -> Union[List[str], str]: ...
    def retrieve_works(self, target_id: int) -> List[IllustInfo]: ...
    def download(self, data: List[IllustInfo], save_path: str) -> None: ...
