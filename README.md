# pixiv-bulk-downloader

[![PyPI](
  <https://img.shields.io/pypi/v/pixiv-bulk-downloader?color=blue>
  )](
  <https://pypi.org/project/pixiv-bulk-downloader/>
) [![CI](
  <https://github.com/eggplants/pixiv-bulk-downloader/actions/workflows/ci.yml/badge.svg>
  )](
  <https://github.com/eggplants/pixiv-bulk-downloader/actions/workflows/ci.yml>
)

[![ghcr size](
  <https://ghcr-badge.egpl.dev/eggplants/pixiv-bulk-downloader/size>
)](
  <https://github.com/eggplants/pixiv-bulk-downloader/pkgs/container/pixiv-bulk-downloader>
)

Pixiv Bulk Downloader for bookmarks and works of following authors.

## Installation

```bash
# mise via github release
mise use -g github:eggplants/pixiv-bulk-downloader

# mise via pipx
mise use -g pipx:pixiv-bulk-downloader

# pipx
pipx install pixiv-bulk-downloader

# pip
pip install pixiv-bulk-downloader
```

### Docker

```bash
docker pull ghcr.io/eggplants/pixiv-bulk-downloader

# the image has no browser, so log in by pasting the code back
docker run --rm -it -v ~/pbd:/root/pbd -v ~/.config/gppt:/root/.config/gppt \
  ghcr.io/eggplants/pixiv-bulk-downloader --oauth bookmarked
```

## Setup

Logging in is delegated to [gppt](https://pypi.org/project/gppt/), which owns the
credentials and the token cache under `~/.config/gppt/`.

```bash
# store an account: pixiv ID + password (e2e), or nothing at all (oauth)
gppt configure
```

## CLI

```shellsession
$ pbd login          # or: pbd l
[+] Opening browser for pixiv login ...
[+] Logged in as: eggplant (@eggplants)

$ pbd following      # or: pbd f -- works of every artist you follow
$ pbd bookmarked     # or: pbd b -- everything you have bookmarked
```

Downloads land in `$SAVE_DIR` (default `~/pbd`), or wherever `-o/--save-dir`
says:

- `<save dir>/following/<id>_<name>_<account>/` -- one directory per artist
- `<save dir>/bookmarks/` -- every bookmarked work

Files already on disk are skipped, so an interrupted run can just be started again.

## Library

```python
from pixiv_bulk_downloader import PixivBookmarksDownloader, login
from pathlib import Path

client = login()
PixivBookmarksDownloader(client, Path.home() / "pbd").download_all()
```

## License

[MIT License](
  <https://github.com/eggplants/pixiv-bulk-downloader/blob/master/LICENSE.txt>
)
