from .base import PixivBaseDownloader
from .bookmarks import PixivBookmarksDownloader
from .followings import PixivFollowingsDownloader
from .pixiv_types import (
    IllustInfo,
    LoginCred,
    LoginFailedError,
    NextBookmarksRequest,
    NextFollowingsRequest,
    UserInfo,
)

__version__ = "3.0.0"
__all__ = [
    "IllustInfo",
    "LoginCred",
    "LoginFailedError",
    "NextBookmarksRequest",
    "NextFollowingsRequest",
    "PixivBaseDownloader",
    "PixivBookmarksDownloader",
    "PixivFollowingsDownloader",
    "UserInfo",
]
