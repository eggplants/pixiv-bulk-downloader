from .pixiv_types import IllustInfo as IllustInfo
from pixivpy3 import AppPixivAPI
from pixivpy3.utils import JsonDict as JsonDict
from typing import Any, List, Union

class PixivBaseDownloader:
    aapi: Any
    login_info: Any
    save_dir: Any
    def __init__(self, aapi: AppPixivAPI, login_info: JsonDict, save_dir: str) -> None: ...
    def refresh(self) -> None: ...
    @staticmethod
    def rand_sleep(base: float = ..., rand: float = ...) -> None: ...
    @staticmethod
    def ext_links(illust: JsonDict) -> Union[List[str], str]: ...
    def retrieve_works(self, target_id: int) -> List[IllustInfo]: ...
    def download(self, data: List[IllustInfo], save_path: str) -> None: ...
