from typing import List, TypedDict, Union


class LoginFailed(Exception):
    pass


class LoginCred(TypedDict):
    pixiv_id: str
    password: str


class IllustInfo(TypedDict):
    id: int
    title: str
    link: Union[str, List[str]]


class UserInfo(TypedDict):
    id: int
    name: str
    account: str
    illusts: List[IllustInfo]


class NextBookmarksRequest(TypedDict):
    user_id: str
    restrict: str
    filter: str
    max_bookmark_id: str


class NextFollowingsRequest(TypedDict):
    user_id: str
    restrict: str
    offset: str
