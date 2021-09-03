import json
import os
from typing import Optional, Tuple

import stdiomask
from gppt import selenium as s
from pixivpy3 import AppPixivAPI
from pixivpy3.utils import JsonDict

from .pixiv_types import LoginCred, LoginFailed


class PixivAuth:
    def __init__(self, auth_json_path: str = 'client.json'):
        self.auth_json_path = auth_json_path

    def auth(self) -> Tuple[AppPixivAPI, JsonDict]:
        cnt = 0
        while cnt < 3:
            try:
                aapi, login_info = self.__auth(cnt)
            except (ValueError, UnboundLocalError):
                print('\x1b[?25h[!]: Failed to login. Check your ID or PW.')
            else:
                return aapi, login_info
            cnt += 1
        else:
            print('[!]: The number of login attempts has been exceeded.')
            raise LoginFailed

    def __auth(self, cnt: int) -> Tuple[AppPixivAPI, JsonDict]:
        aapi: AppPixivAPI = AppPixivAPI()
        login_cred: Optional[LoginCred] = self.read_client_cred()

        if login_cred is not None and cnt == 0:
            ref = self.get_refresh_token(
                login_cred['pixiv_id'], login_cred['password'])
            print('\x1b[?25l[+]: Login...')
            login_info = aapi.auth(refresh_token=ref)
        elif login_cred is None or cnt > 0:
            print('[+]: ID is mail address, userid, account name.')
            stdin_login = (stdiomask.getpass(prompt='[?]: ID: '),
                           stdiomask.getpass(prompt='[?]: PW: '))
            print('\x1b[?25l[+]: Login...', end='\r')
            ref = self.get_refresh_token(stdin_login[0], stdin_login[1])
            login_info = aapi.auth(refresh_token=ref)
            print('\033[K[+]: Login...OK!')
        else:
            raise LoginFailed

        return (aapi, login_info)

    @staticmethod
    def get_refresh_token(pixiv_id: str, pixiv_pass: str) -> str:
        gpt = s.GetPixivToken(headless=True, user=pixiv_id, pass_=pixiv_pass)
        res = gpt.login()
        return res["refresh_token"]

    def read_client_cred(self) -> Optional[LoginCred]:
        if os.path.exists(self.auth_json_path):
            cred_data = json.load(open(self.auth_json_path, 'r'))
            if set(cred_data.keys()) == {'pixiv_id', 'password'}:
                return cred_data
            else:
                return None
        else:
            return None
