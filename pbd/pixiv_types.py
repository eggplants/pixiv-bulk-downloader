from __future__ import annotations

from typing import TypedDict


class LoginFailed(Exception):
    pass


class LoginCred(TypedDict):
    pixiv_id: str
    password: str


class IllustInfo(TypedDict):
    id: int
    title: str
    link: str | list[str]


class UserInfo(TypedDict):
    id: int
    name: str
    account: str
    illusts: list[IllustInfo]


class NextBookmarksRequest(TypedDict):
    user_id: str
    restrict: str
    filter: str
    max_bookmark_id: str


class NextFollowingsRequest(TypedDict):
    user_id: str
    restrict: str
    offset: str
