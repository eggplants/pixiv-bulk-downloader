from __future__ import annotations

import pytest
from conftest import FakeAPI, make_client
from gppt import LoginError

import pixiv_bulk_downloader.cli as cli_module
from pixiv_bulk_downloader import __version__
from pixiv_bulk_downloader.auth import DEFAULT_PROFILE
from pixiv_bulk_downloader.cli import main, parse_args


@pytest.fixture
def logged_in(monkeypatch):
    """Replace the login with a client whose downloads are recorded."""
    api = FakeAPI(detail={"profile": {"total_follow_users": 3, "total_illust_bookmarks_public": 5}})
    client = make_client(api)
    seen = {"downloads": [], "limits": []}

    def fake_login(profile, **kwargs):
        seen["profile"] = profile
        seen.update(kwargs)
        return client

    class Recorder:
        def __init__(self, _client, save_dir):
            self.save_dir = save_dir

        def download_all(self, limit=None):
            seen["downloads"].append((type(self).__name__, self.save_dir))
            seen["limits"].append(limit)

    monkeypatch.setattr(cli_module, "login", fake_login)
    monkeypatch.setattr(cli_module, "PixivFollowingsDownloader", type("Following", (Recorder,), {}))
    monkeypatch.setattr(cli_module, "PixivBookmarksDownloader", type("Bookmarked", (Recorder,), {}))
    return seen


def test_version_flag_prints_the_version(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["--version"])
    assert excinfo.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_defaults_are_filled_in_without_a_subcommand():
    parsed = parse_args([])
    assert parsed.command is None
    assert parsed.profile == DEFAULT_PROFILE
    assert parsed.method is None
    assert parsed.headless is True
    assert parsed.force is False
    assert parsed.save_dir == cli_module.DEFAULT_SAVE_DIR
    assert parsed.limit is None


def test_options_may_come_before_the_subcommand(tmp_path):
    parsed = parse_args(["-o", str(tmp_path), "-p", "alt", "following"])
    assert (parsed.command, parsed.profile, parsed.save_dir) == ("following", "alt", tmp_path)


def test_options_after_the_subcommand_win(tmp_path):
    parsed = parse_args(["-o", str(tmp_path / "before"), "following", "-o", str(tmp_path / "after")])
    assert parsed.save_dir == tmp_path / "after"


@pytest.mark.parametrize("command", ["login", "l"])
def test_login_only_logs_in(logged_in, command):
    assert main([command]) == 0
    assert logged_in["downloads"] == []


@pytest.mark.parametrize("command", ["following", "f"])
def test_following_downloads_the_following(logged_in, command, tmp_path):
    assert main([command, "-o", str(tmp_path)]) == 0
    assert logged_in["downloads"] == [("Following", tmp_path)]


@pytest.mark.parametrize("command", ["bookmarked", "b"])
def test_bookmarked_downloads_the_bookmarks(logged_in, command, tmp_path):
    assert main([command, "-o", str(tmp_path)]) == 0
    assert logged_in["downloads"] == [("Bookmarked", tmp_path)]


def test_login_options_reach_the_login(logged_in):
    assert main(["-p", "alt", "--oauth", "--no-headless", "-f", "login"]) == 0
    assert logged_in["profile"] == "alt"
    assert (logged_in["method"], logged_in["headless"], logged_in["force"]) == ("oauth", False, True)


def test_bare_invocation_asks_before_each_download(monkeypatch, logged_in, tmp_path):
    answers = iter(["y", "n"])
    asked = []

    def fake_input(prompt):
        asked.append(prompt)
        return next(answers)

    monkeypatch.setattr("builtins.input", fake_input)

    assert main(["-o", str(tmp_path)]) == 0

    assert logged_in["downloads"] == [("Following", tmp_path)]
    assert "3 artists" in asked[0]
    assert "5 works" in asked[1]


def test_yes_skips_the_prompts(logged_in, tmp_path):
    assert main(["-y", "-o", str(tmp_path)]) == 0
    assert logged_in["downloads"] == [("Following", tmp_path), ("Bookmarked", tmp_path)]


def test_a_failed_login_is_reported_not_raised(monkeypatch, capsys):
    def boom(*args, **kwargs):
        msg = "no authorization code"
        raise LoginError(msg)

    monkeypatch.setattr(cli_module, "login", boom)

    assert main(["login"]) == 1
    assert "Login failed: no authorization code" in capsys.readouterr().err


def test_an_interrupt_is_reported_not_raised(monkeypatch, capsys):
    def boom(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(cli_module, "login", boom)

    assert main([]) == 1
    assert "SIGINT" in capsys.readouterr().err


@pytest.mark.parametrize("args", [["f", "-l", "10"], ["f", "--limit", "10"], ["-l", "10", "f"]])
def test_limit_is_accepted_on_either_side_of_the_subcommand(args):
    assert parse_args(args).limit == 10


@pytest.mark.parametrize("value", ["0", "-1", "many"])
def test_limit_has_to_be_a_positive_integer(value, capsys):
    with pytest.raises(SystemExit):
        parse_args(["f", "-l", value])
    assert "--limit" in capsys.readouterr().err


def test_limit_reaches_the_following_downloader(logged_in, tmp_path):
    assert main(["f", "-o", str(tmp_path), "-l", "3"]) == 0
    assert logged_in["limits"] == [3]


def test_without_a_limit_the_following_downloader_gets_none(logged_in, tmp_path):
    assert main(["f", "-o", str(tmp_path)]) == 0
    assert logged_in["limits"] == [None]


@pytest.mark.parametrize("args", [["b", "-l", "10"], ["-l", "10", "b"]])
def test_the_bookmarked_command_takes_a_limit_too(args):
    assert parse_args(args).limit == 10


def test_limit_reaches_the_bookmarks_downloader(logged_in, tmp_path):
    assert main(["b", "-o", str(tmp_path), "-l", "3"]) == 0
    assert logged_in["limits"] == [3]


def test_a_bare_run_passes_the_limit_on_to_both_downloads(logged_in, tmp_path):
    assert main(["-y", "-l", "4", "-o", str(tmp_path)]) == 0
    assert logged_in["limits"] == [4, 4]


def test_the_prompts_mention_the_limit(monkeypatch, logged_in, tmp_path):
    asked = []
    monkeypatch.setattr("builtins.input", lambda prompt: asked.append(prompt) or "n")

    assert main(["-l", "4", "-o", str(tmp_path)]) == 0
    assert "4 of 3 artists" in asked[0]
    assert "4 of 5 works" in asked[1]
