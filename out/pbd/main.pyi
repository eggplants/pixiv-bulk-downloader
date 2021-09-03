from .auth import PixivAuth as PixivAuth
from .bookmarks import PixivBookmarksDownloader as PixivBookmarksDownloader
from .followings import PixivFollowingsDownloader as PixivFollowingsDownloader
from .types import LoginFailed as LoginFailed
from typing import Any

SAVE_DIR: Any

def all_yes(f, b) -> None: ...
def interact(f, b, aapi): ...
def main() -> None: ...
