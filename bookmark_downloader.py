import json
import os
from getpass import getpass

from pixivpy3 import AppPixivAPI, PixivAPI

"""client.json
{
  "pixiv_id" : "<change this>",
  "password" : "<change this>"
}
"""


def auth(api):
    login_cred = (json.load(open("client.json", "r"))
                  if os.path.exists("client.json") else '')
    # login with account info json file
    if login_cred != '':
        login_info = api.login(
            login_cred["pixiv_id"], login_cred["password"])
        aapi = AppPixivAPI()
        aapi.login(login_cred["pixiv_id"], login_cred["password"])
    else:
        print("[+]ID is mail address, userid, account name.")
        stdin_login = (input("[+]ID: "), getpass("[+]Password: "))
        login_info = api.login(stdin_login[0], stdin_login[1])
        aapi = AppPixivAPI()
        aapi.login(stdin_login[0], stdin_login[1])

    return (aapi, login_info)


def retrieve_bookmarks(api, login_info):
    def ext_links(illust):
        links = [page.image_urls.original for page in illust.meta_pages]
        link = illust.meta_single_page.get(
            'original_image_url', illust.image_urls.large)
        return (links if links != [] else link)

    urls, next, target_id = [], "", login_info.response.user.id
    while True:
        # pagenation
        res_json = (api.user_bookmarks_illust(target_id)
                    if next == "" else api.user_bookmarks_illust(**next))
        urls.extend([
            {
                "id": illust.id,
                "title": illust.title,
                "link": ext_links(illust)}
            for illust in res_json["illusts"]])
        next = api.parse_qs(res_json["next_url"])
        if not next:
            break

    return urls


def download(aapi, bookmarked_data, save_dir="./pixivpy/my_bookmarks"):
    os.makedirs(save_dir, exist_ok=True)
    bookmark_len = len(bookmarked_data)
    for idx, image_data in enumerate(bookmarked_data):
        print(
            "[{}/{}]: {}({})".format(
                idx + 1, bookmark_len,
                image_data["title"], image_data["id"]))
        if type(image_data["link"]) is list:
            for image_url in image_data["link"]:
                print(image_url.split("/")[-1], end="\r")
                aapi.download(image_url, path=save_dir)
        else:
            print(image_data["link"].split("/")[-1], end="\r")
            aapi.download(image_data["link"], path=save_dir)


if __name__ == '__main__':
    api = PixivAPI()
    api.hosts = "https://app-api.pixiv.net"
    aapi, login_info = auth(api)
    bookmarked_data = retrieve_bookmarks(aapi, login_info)
    download(aapi, bookmarked_data)
