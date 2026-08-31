from __future__ import annotations

from pixiv_bulk_downloader import console


def test_info_prefixes_the_line(capsys):
    console.info("hello")
    assert capsys.readouterr().out == f"{console.CLEAR_LINE}[+]: hello\n"


def test_warn_goes_to_stderr(capsys):
    console.warn("oops")
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == f"{console.CLEAR_LINE}[!]: oops\n"


def test_status_stays_on_one_line(capsys):
    console.status("working")
    assert capsys.readouterr().out.endswith("\r")


def test_clear_line_erases_without_moving_up(capsys):
    console.clear_line()
    assert capsys.readouterr().out == f"{console.CLEAR_LINE}\r"


def test_counter_pads_both_numbers_to_the_total_width():
    assert console.counter(3, 100) == "[003/100]"
    assert console.counter(1, 2) == "[1/2]"
