""".. include:: ../README.md"""  # noqa: D415

from __future__ import annotations

import importlib.metadata

try:
    __version__ = importlib.metadata.version(__name__)
except importlib.metadata.PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0"

from .auth import PixivClient, login
from .base import PixivAPIError, PixivBaseDownloader
from .bookmarks import PixivBookmarksDownloader
from .cache import CACHE_FILENAME, WorkCache
from .followings import PixivFollowingsDownloader
from .models import ArtistInfo, IllustInfo

__all__ = [
    "CACHE_FILENAME",
    "ArtistInfo",
    "IllustInfo",
    "PixivAPIError",
    "PixivBaseDownloader",
    "PixivBookmarksDownloader",
    "PixivClient",
    "PixivFollowingsDownloader",
    "WorkCache",
    "__version__",
    "login",
]
