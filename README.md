# pixiv-bulk-downloader

[![PyPI version](https://badge.fury.io/py/pixiv-bulk-downloader.svg)](https://badge.fury.io/py/pixiv-bulk-downloader) [![Docker Image Size (latest by date)](https://img.shields.io/docker/image-size/eggplanter/pbd)](https://hub.docker.com/r/eggplanter/pbd) [![Maintainability](https://api.codeclimate.com/v1/badges/f4083498009bd92d2d05/maintainability)](https://codeclimate.com/github/eggplants/pixiv-bulk-downloader/maintainability)

Pixiv Bulk Downloader

## Feature

- Download
  - works of following users
    - SAVE: `$HOME/pbd/following`
  - bookmarked works
    - SAVE: `$HOME/pbd/bookmarks`

## Try

### From PyPI

Note: _In advance, please setup google-chrome-stable + selenium + webdriver_

```bash
# pip 3.x
❭ pip install pixiv-bulk-downloader
# run
❭ pbd
[+]: ID is mail address, userid, account name.
[?]: ID:
[?]: PW:
[+]: Login...OK!
[?]: Download all works of following? (766 artists) (n/y):
[?]: Download all bookmarked? (1909 works) (n/y):
```

### From Docker

```bash
❭ docker run -it -v ~/pbd:/root/pbd eggplanter/pbd
[+]: ID is mail address, userid, account name.
...
```

## Capture

![image](https://user-images.githubusercontent.com/42153744/132086056-82a4e3e8-bbdd-42bc-8296-716ce4c34edb.png)

![image](https://user-images.githubusercontent.com/42153744/132086168-ce4d8ae1-9085-4c7a-ba9f-4ae8f9a17757.png)

![image](https://user-images.githubusercontent.com/42153744/132086124-7a7634f9-7fe0-47b9-98b5-840716c4db34.png)

![image](https://user-images.githubusercontent.com/42153744/132086141-b0b82493-ed7d-44a6-80c8-dea7c47297a1.png)

## License

MIT
