# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Pixiv Bulk Downloader for bookmarks and works of following authors.

## Commands

Dependencies are managed with [uv](https://docs.astral.sh/uv/) and every task is
defined in `mise.toml`, which is the canonical list.

```bash
uv sync --all-groups                   # install runtime + dev + docs groups
mise run pytest                        # run the test suite
uv run pytest tests/test_pixiv_bulk_downloader.py::test_version_is_available  # a single test
mise run ruff                          # format + autofix (uv format)
mise run ty                            # type check (uvx ty check)
mise run pymarkdown                    # markdown lint
mise run pyproject-fmt                 # normalize pyproject.toml
mise run pre-commit                    # ruff + ty + pymarkdown + pyproject-fmt
mise run ci                            # pre-commit + pytest-cov -- what CI runs
mise run build                         # build sdist + wheel
mise run docs                          # pdoc API docs into ./docs
mise run pinup                         # update the pinned action/image digests
mise run build-binary                  # PyInstaller standalone binary into ./dist
```

The venv is tied to the absolute repo path (`uv sync` bakes it into script shebangs). If the
repo directory gets renamed or moved, delete `.venv/` and `uv sync` again rather than debugging
"No such file or directory" / `ModuleNotFoundError` -- it is a stale interpreter path, not a
code bug.

Lint config lives in `pyproject.toml`: Ruff with `lint.select = ["ALL"]` and `line-length = 120`.
Prefer a targeted `lint.per-file-ignores` entry with a comment over a scattered `# noqa`.

## Architecture

Authentication is delegated to [gppt](https://pypi.org/project/gppt/) v5 -- it owns the
credentials, the login browser and the token cache under `~/.config/gppt/`. The pixiv API
itself is `pixivpy3`.

- **`pixiv_bulk_downloader/__init__.py`** -- package version, read from the installed
  distribution metadata (`0.0.0` when running from a source tree with no tags), plus the
  public re-exports.
- **`pixiv_bulk_downloader/cli.py`** -- argparse entry point (`pbd`) with the `login`/`l`,
  `following`/`f` and `bookmarked`/`b` subcommands; a bare `pbd` logs in and then asks what
  to download. `main()` takes an optional argument list so the tests can drive it without
  touching `sys.argv`, and returns the exit code.
- **`pixiv_bulk_downloader/auth.py`** -- `login()` wraps `gppt.get_token`, and `PixivClient`
  keeps an `AppPixivAPI` authenticated, refreshing the access token when a long run outlives
  it.
- **`pixiv_bulk_downloader/base.py`** -- `PixivBaseDownloader`: paging over an endpoint by
  feeding each `next_url` query string back into the API method, plus the actual downloads.
- **`pixiv_bulk_downloader/bookmarks.py`** / **`followings.py`** -- the two concrete
  downloaders, saving into `<save dir>/bookmarks` and `<save dir>/following/<artist>`.
- **`pixiv_bulk_downloader/console.py`** -- every line the tool prints. The `T201`
  per-file-ignore lives here so nothing else needs one.
- **`pixiv_bulk_downloader/models.py`** -- the `TypedDict`s the downloaders pass around.
- **`pixiv_bulk_downloader/__main__.py`** -- makes `python -m pixiv_bulk_downloader` work.

The sleeps between requests are not decoration: walking a whole following list is one request
per artist plus one per page of their works, and pixiv rate-limits it long before it finishes.
The intervals are module constants (`FOLLOWING_INTERVAL`, `WORKS_PAGE_INTERVAL`,
`BOOKMARKS_PAGE_INTERVAL`); tests stub `PixivBaseDownloader.rand_sleep` out.

## Versioning and releases

Versions come from git tags via `uv-dynamic-versioning`; nothing in the repo hard-codes one.
Pushing a `v*.*.*` tag runs `build-binaries.yml`, which builds one binary per OS/arch on native
runners (PyInstaller cannot cross-compile), attaches them to a **draft** release and publishes it
afterwards -- immutable releases lock the assets of an already published release. `release.yml`
then reacts to `release: [published]` and does the PyPI and GHCR publish.

## Testing conventions

Tests live in `tests/` and mirror the module split 1:1. `tests/**` has its own
`lint.per-file-ignores` block, so assertions and missing annotations are fine there.

`tests/conftest.py` holds the stand-ins: `FakeAPI` (an `AppPixivAPI` that serves canned
pages and records what was downloaded), `Attr` (a dict with attribute access, like pixivpy's
`JsonDict`), and `make_client`, which is where the one `cast` to `AppPixivAPI` lives. Nothing
in the suite touches the network.
