from pixivpy3 import AppPixivAPI
from typing import Any, Optional, Tuple, TypedDict

class PixivLoginFailed(Exception): ...

class LoginCred(TypedDict):
    pixiv_id: str
    password: str

class ProfileURIs(TypedDict):
    px_16x16: str
    px_50x50: str
    px_170x170: str

class LoginUserInfo(TypedDict):
    profile_image_urls: ProfileURIs
    id: str
    name: str
    account: str
    mail_address: str
    is_premium: bool
    x_restrict: int
    is_mail_authorized: bool

class OAuthAPIResponse(TypedDict):
    access_token: str
    expires_in: int
    token_type: str
    scope: str
    refresh_token: str
    user: LoginUserInfo

class LoginInfo(TypedDict):
    access_token: str
    expires_in: int
    token_type: str
    scope: str
    refresh_token: str
    user: LoginUserInfo
    response: OAuthAPIResponse

class PixivAuth:
    auth_json_path: Any
    def __init__(self, auth_json_path: str = ...) -> None: ...
    def auth(self) -> Tuple[AppPixivAPI, LoginInfo]: ...
    @staticmethod
    def get_refresh_token(pixiv_id: str, pixiv_pass: str) -> str: ...
    def read_client_cred(self) -> Optional[LoginCred]: ...
