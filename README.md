# pixiv-bulk-downloader

[![PyPI version](
  https://badge.fury.io/py/pixiv-bulk-downloader.svg
  )](
  https://badge.fury.io/py/pixiv-bulk-downloader
) [![Maintainability](
  https://api.codeclimate.com/v1/badges/f4083498009bd92d2d05/maintainability
  )](https://codeclimate.com/github/eggplants/pixiv-bulk-downloader/maintainability
) [![pre-commit.ci status](
  https://results.pre-commit.ci/badge/github/eggplants/pixiv-bulk-downloader/main.svg
  )](
  https://results.pre-commit.ci/latest/github/eggplants/pixiv-bulk-downloader/main
)


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

<details>

<summary>Ubuntu</summary>

```bash
# google-chrome-stable
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install ./google-chrome-stable_current_amd64.deb -y
google-chrome --version  # check

# selenium
pip install selenium
python -c'import selenium;print("selenium", selenium.__version__)'  # check

# webdriver
pip install chromedriver-binary-auto
# add this to rc or env: export PATH="$PATH:`chromedriver-path`"
chromedriver -v  # check
```

</details>

```bash
# Python>=3.9
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
❭ docker run -it -v ~/pbd:/root/pbd ghcr.io/eggplants/pixiv-bulk-downloader
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
