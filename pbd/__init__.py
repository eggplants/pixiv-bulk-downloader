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

__version__ = "2.3"
__all__ = [
    "PixivBaseDownloader",
    "PixivBookmarksDownloader",
    "IllustInfo",
    "LoginCred",
    "LoginFailed",
    "NextBookmarksRequest",
    "NextFollowingsRequest",
    "UserInfo",
]
