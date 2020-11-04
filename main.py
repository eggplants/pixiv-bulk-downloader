import json
import os
from getpass import getpass

from pixivpy3 import AppPixivAPI, PixivAPI
from pixivpy3.utils import PixivError

'''client.json
{
  'pixiv_id' : '<change this>',
  'password' : '<change this>'
}
'''


def auth():
    login_cred = (json.load(open('client.json', 'r'))
                  if os.path.exists('client.json') else '')
    api = PixivAPI()
    api.hosts = 'https://app-api.pixiv.net'
    if login_cred != '':
        login_info = api.login(
            login_cred['pixiv_id'], login_cred['password'])
        aapi = AppPixivAPI()
        aapi.login(login_cred['pixiv_id'], login_cred['password'])
    else:
        print('[+]ID is mail address, userid, account name.')
        stdin_login = (input('[+]ID: '), getpass('[+]Password: '))
        login_info = api.login(stdin_login[0], stdin_login[1])
        aapi = AppPixivAPI()
        aapi.login(stdin_login[0], stdin_login[1])

    return (api, aapi, login_info)


def retrieve_bookmarks(api, login_info):
    def ext_links(illust):
        links = [page.image_urls.original for page in illust.meta_pages]
        link = illust.meta_single_page.get(
            'original_image_url', illust.image_urls.large)

        return (links if links != [] else link)

    urls, next, target_id = [], '', login_info.response.user.id
    while True:
        # pagenation
        res_json = (api.user_bookmarks_illust(target_id)
                    if next == '' else api.user_bookmarks_illust(**next))
        urls.extend([
            {
                'id': illust.id,
                'title': illust.title,
                'link': ext_links(illust)}
            for illust in res_json['illusts']])
        next = api.parse_qs(res_json['next_url'])
        if not next:
            break

    return urls


def retrieve_works(api, id_):
    def ext_links(illust):
        links = [page.image_urls.original for page in illust.meta_pages]
        link = illust.meta_single_page.get(
            'original_image_url', illust.image_urls.large)

        return (links if links != [] else link)

    # pagenation
    urls, next, target_id = [], '', id_
    while True:
        # pagenation
        res_json = (api.user_illusts(target_id, type='illust')
                    if next == '' else api.user_illusts(**next))
        urls.extend([{
                'id': illust.id,
                'title': illust.title,
                'link': ext_links(illust)}
            for illust in res_json['illusts']])
        next = api.parse_qs(res_json['next_url'])
        if not next:
            break

    return urls


def retrieve_following(api, login_info):
    users = []
    res_json = api.user_following(login_info.response.user.id)
    for user in res_json.user_previews:
        user_info = user.user
        users.append({
            "id": user_info.id,
            "name": user_info.name,
            "account": user_info.account,
            "illusts": retrieve_works(api, user_info.id)})

    return users


SAVE_DIR = os.path.join(os.path.expanduser("~"), 'pbd')

def download(api, data, save_dir=SAVE_DIR):
    os.makedirs(save_dir, exist_ok=True)
    data_len = len(data)
    for idx, image_data in enumerate(data):
        title, id_ = image_data['title'].replace('/', '／'), image_data['id']
        link = image_data['link']
        print('[{}/{}]: {}({})'.format(idx + 1, data_len, title, id_))
        if type(link) is list:
            for _ in link:
                basename_ = _.split('/')[-1]
                fname = '{}_{}_{}'.format(id_, title, basename_.split('_')[-1])
                print(fname, end="\r")
                api.download(_, path=save_dir,fname=fname)
        else:
            basename_ = link.split('/')[-1]
            fname = '{}_{}_{}'.format(id_, title, basename_.split('_')[-1])
            print(fname, end="\r")
            api.download(link, path=save_dir, fname=fname)


def get_all_following_works(aapi, login_info):
    following_data = retrieve_following(aapi, login_info)
    following_len = len(following_data)
    for idx, author_data in enumerate(following_data):
        dirname = '{}_{}_{}'.format(
            author_data['id'], author_data['name'],
            author_data['account']).replace('/', '／')
        print('[{}/{}]: {}'.format(idx + 1, following_len, dirname))
        download(aapi, author_data['illusts'],
                 os.path.join(SAVE_DIR, 'following', dirname))


def get_all_bookmarked_works(aapi, login_info):
    bookmarked_data = retrieve_bookmarks(aapi, login_info)
    download(aapi, bookmarked_data, os.path.join(SAVE_DIR, 'bookmarks'))


def main():
    try:
        api, aapi, login_info = auth()
    except PixivError as e:
        print(e.reason)
        exit(1)

    try:
        if input('get_all_following_works? [yn]: ') == 'y':
            get_all_following_works(aapi, login_info)
        if input('get_all_bookmarked_works? [yn]: ') == 'y':
            get_all_bookmarked_works(aapi, login_info)
    except KeyError as e:
        print(e, 'Request limit seem to be exceeded.')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
