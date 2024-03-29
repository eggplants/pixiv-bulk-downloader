from .base import PixivBaseDownloader
from .bookmarks import PixivBookmarksDownloader
from .followings import PixivFollowingsDownloader
from .pixiv_types import (
    IllustInfo,
    LoginCred,
    LoginFailed,
    NextBookmarksRequest,
    NextFollowingsRequest,
    UserInfo,
)

__version__ = "2.8.1"
__all__ = [
    "PixivBaseDownloader",
    "PixivBookmarksDownloader",
    "PixivFollowingsDownloader",
    "IllustInfo",
    "LoginCred",
    "LoginFailed",
    "NextBookmarksRequest",
    "NextFollowingsRequest",
    "UserInfo",
]
