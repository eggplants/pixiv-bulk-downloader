from .auth import PixivAuth as PixivAuth
from .bookmarks import PixivBookmarksDownloader as PixivBookmarksDownloader
from .followings import PixivFollowingsDownloader as PixivFollowingsDownloader
from .pixiv_types import LoginFailed as LoginFailed
from pixivpy3.aapi import AppPixivAPI as AppPixivAPI
from typing import Any

SAVE_DIR: Any

def interact(aapi: AppPixivAPI, f: PixivFollowingsDownloader, b: PixivBookmarksDownloader) -> None: ...
def main() -> None: ...
