"""Command line entry point for pixiv-bulk-downloader."""

from __future__ import annotations

import os
import shutil
from argparse import SUPPRESS, ArgumentDefaultsHelpFormatter, ArgumentParser, Namespace, RawDescriptionHelpFormatter
from pathlib import Path

from gppt import LoginError, TokenError
from pixivpy3.utils import PixivError

from . import __version__, console
from .auth import DEFAULT_PROFILE, PixivClient, login
from .base import PixivAPIError
from .bookmarks import PixivBookmarksDownloader
from .followings import PixivFollowingsDownloader

DEFAULT_SAVE_DIR = Path(os.environ.get("SAVE_DIR") or Path.home() / "pbd")
"""Where downloads go unless `--save-dir` says otherwise."""

DESCRIPTION = """\
Pixiv Bulk Downloader for bookmarks and works of following authors.

Run without a subcommand to log in and then be asked what to download.
Credentials and tokens are handled by gppt; `gppt configure` stores them.
"""

_DEFAULTS = {
    "profile": DEFAULT_PROFILE,
    "method": None,
    "headless": True,
    "force": False,
    "save_dir": DEFAULT_SAVE_DIR,
}


class HelpFormatter(ArgumentDefaultsHelpFormatter, RawDescriptionHelpFormatter):
    """Show argument defaults while keeping the description's own line breaks."""


def _shared_parser(*, save_dir: bool) -> ArgumentParser:
    """Build the options accepted both before and after the subcommand.

    Every default is `SUPPRESS` so that `pbd -o dir following` keeps the value
    given before the subcommand: argparse copies each attribute of the
    subparser's namespace onto the main one, defaults included. The real
    defaults are applied by `parse_args` afterwards.

    Args:
        save_dir: Whether to include the download options too.

    Returns:
        A parser meant to be passed as a `parents=` entry.
    """
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-p",
        "--profile",
        default=SUPPRESS,
        help=f"gppt profile to log in with (default: {DEFAULT_PROFILE})",
    )
    parser.add_argument(
        "--no-headless",
        dest="headless",
        action="store_false",
        default=SUPPRESS,
        help="show the login browser window (default: hidden)",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        default=SUPPRESS,
        help="ignore the cached token and log in again",
    )
    method = parser.add_mutually_exclusive_group()
    method.add_argument(
        "--e2e",
        dest="method",
        action="store_const",
        const="e2e",
        default=SUPPRESS,
        help="log in by driving a browser with the profile's stored credentials",
    )
    method.add_argument(
        "--oauth",
        dest="method",
        action="store_const",
        const="oauth",
        default=SUPPRESS,
        help="log in in your own browser and paste the code back (OAuth2 PKCE)",
    )
    if save_dir:
        parser.add_argument(
            "-o",
            "--save-dir",
            type=Path,
            default=SUPPRESS,
            help=f"directory to download into (default: {DEFAULT_SAVE_DIR})",
        )
    return parser


def parse_args(args: list[str] | None = None) -> Namespace:
    """Parse the command line.

    Args:
        args: Arguments to parse instead of `sys.argv[1:]`. Used by the tests.

    Returns:
        The parsed arguments, with the defaults of the shared options filled in.
    """
    auth_only = _shared_parser(save_dir=False)
    downloading = _shared_parser(save_dir=True)

    def formatter(prog: str) -> HelpFormatter:
        return HelpFormatter(
            prog,
            width=shutil.get_terminal_size(fallback=(120, 50)).columns,
            max_help_position=40,
        )

    parser = ArgumentParser(
        prog="pbd",
        description=DESCRIPTION,
        parents=[downloading],
        formatter_class=formatter,
    )
    parser.add_argument("-y", "--yes", action="store_true", help="answer yes to every prompt")
    parser.add_argument("-V", "--version", action="version", version=f"%(prog)s {__version__}")

    sub = parser.add_subparsers(dest="command")
    sub.add_parser(
        "login",
        aliases=["l"],
        parents=[auth_only],
        formatter_class=formatter,
        help="log in to pixiv and cache the token",
    )
    sub.add_parser(
        "following",
        aliases=["f"],
        parents=[downloading],
        formatter_class=formatter,
        help="download the works of every artist you follow",
    )
    sub.add_parser(
        "bookmarked",
        aliases=["b"],
        parents=[downloading],
        formatter_class=formatter,
        help="download every work you have bookmarked",
    )

    parsed = parser.parse_args(args)
    for name, value in _DEFAULTS.items():
        if not hasattr(parsed, name):
            setattr(parsed, name, value)
    return parsed


def main(args: list[str] | None = None) -> int:
    """Run the command.

    Args:
        args: Arguments to parse instead of `sys.argv[1:]`. Used by the tests.

    Returns:
        The process exit code.
    """
    parsed = parse_args(args)
    try:
        return _run(parsed)
    except (LoginError, TokenError) as exc:
        console.warn(f"Login failed: {exc}")
    except (PixivAPIError, PixivError) as exc:
        console.warn(f"pixiv refused the request: {exc}")
    except KeyboardInterrupt:
        console.warn("SIGINT")
    finally:
        console.show_cursor()
    return 1


def _run(parsed: Namespace) -> int:
    """Log in, then do whatever the subcommand asked for."""
    client = login(
        parsed.profile,
        method=parsed.method,
        headless=parsed.headless,
        force=parsed.force,
    )
    console.info(f"Logged in as: {client.token.user_name} (@{client.token.user_account})")

    if parsed.command in {"login", "l"}:
        return 0
    if parsed.command in {"following", "f"}:
        PixivFollowingsDownloader(client, parsed.save_dir).download_all()
    elif parsed.command in {"bookmarked", "b"}:
        PixivBookmarksDownloader(client, parsed.save_dir).download_all()
    else:
        _interact(client, parsed.save_dir, yes=parsed.yes)
    console.info("Finish!")
    return 0


def _interact(client: PixivClient, save_dir: Path, *, yes: bool) -> None:
    """Ask what to download, showing how much of it there is."""
    profile = client.aapi.user_detail(client.user_id)["profile"]
    following = f"Download all works of following? ({profile['total_follow_users']} artists)"
    bookmarked = f"Download all bookmarked works? ({profile['total_illust_bookmarks_public']} works)"
    if yes or console.ask(following):
        PixivFollowingsDownloader(client, save_dir).download_all()
    if yes or console.ask(bookmarked):
        PixivBookmarksDownloader(client, save_dir).download_all()


if __name__ == "__main__":
    raise SystemExit(main())
