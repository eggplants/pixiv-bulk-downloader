"""Terminal output helpers.

Every line the tool prints goes through here, so the ANSI escapes and the
`[+]:` / `[!]:` prefixes live in one place instead of being spread over the
downloaders.
"""

from __future__ import annotations

import sys

CLEAR_LINE = "\033[K"
"""Erase from the cursor to the end of the line."""

CURSOR_UP = "\033[A"
SHOW_CURSOR = "\033[?25h"


def info(message: str) -> None:
    """Print a normal progress line."""
    print(f"{CLEAR_LINE}[+]: {message}")


def warn(message: str) -> None:
    """Print a problem to stderr."""
    print(f"{CLEAR_LINE}[!]: {message}", file=sys.stderr)


def status(message: str) -> None:
    """Print a line the next `status` (or `drop_line`) call overwrites."""
    print(f"{CLEAR_LINE}{message}", end="\r", flush=True)


def clear_line() -> None:
    """Erase the current line, leaving the cursor at its start.

    Ends a run of `status` lines so the last one does not linger.
    """
    print(f"{CLEAR_LINE}", end="\r", flush=True)


def drop_line() -> None:
    """Erase the current line and the one above it, leaving the cursor there.

    Used to keep a transient per-item line from piling up in the scrollback.
    """
    print(f"{CLEAR_LINE}{CURSOR_UP}{CLEAR_LINE}", end="", flush=True)


def show_cursor() -> None:
    """Undo a cursor hidden by an interrupted download."""
    print(SHOW_CURSOR, end="")


def counter(index: int, total: int) -> str:
    """Render a zero-padded `[3/42]` progress counter.

    Args:
        index: 1-based position of the current item.
        total: How many items there are in all.

    Returns:
        The counter, both numbers padded to the width of `total`.
    """
    width = len(str(total))
    return f"[{index:0{width}d}/{total:0{width}d}]"
