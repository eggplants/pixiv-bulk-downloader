from .base import PixivBaseDownloader as PixivBaseDownloader
from .pixiv_types import IllustInfo as IllustInfo, NextBookmarksRequest as NextBookmarksRequest
from pixivpy3.utils import JsonDict as JsonDict
from typing import List

class PixivBookmarksDownloader(PixivBaseDownloader):
    def get_all_bookmarked_works(self) -> None: ...
    def retrieve_bookmarks(self) -> List[IllustInfo]: ...
