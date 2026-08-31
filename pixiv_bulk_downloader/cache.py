"""SQLite cache of the work listings a following run has already walked.

Listing one artist costs a request per page of their works, and `pbd
following` walks every artist's whole listing, newest work first, on every
run. Once an artist has been listed to the end the listing is written here, so
the next run only pages until it meets a work it already has: everything past
that point is what the cache holds.

The database is a single file in the save directory. Deleting it costs nothing
but the next run walking every listing in full again.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence
    from pathlib import Path
    from types import TracebackType

    from .models import IllustInfo

CACHE_FILENAME = "pbd-cache.sqlite3"
"""Name of the database, kept in the save directory."""

_SCHEMA = """
CREATE TABLE IF NOT EXISTS artists (
    artist_id  INTEGER PRIMARY KEY,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS works (
    artist_id INTEGER NOT NULL REFERENCES artists (artist_id) ON DELETE CASCADE,
    position  INTEGER NOT NULL,
    illust_id INTEGER NOT NULL,
    title     TEXT NOT NULL,
    links     TEXT NOT NULL,
    PRIMARY KEY (artist_id, illust_id)
);
CREATE INDEX IF NOT EXISTS works_position ON works (artist_id, position);
"""


class WorkCache:
    """The listings of every artist a run has walked to the end.

    An artist only gets a row once their listing has been walked in full, so a
    run that dies halfway leaves nothing behind and the next one starts over
    rather than trusting half a listing.
    """

    def __init__(self, path: Path) -> None:
        """Name the database file without opening it yet.

        Args:
            path: The database file; it and its parents are created on the
                first read or write, not here.
        """
        self.path = path
        self._conn: sqlite3.Connection | None = None

    def __enter__(self) -> Self:
        """Return the cache itself; the connection is still opened lazily."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Close the connection when the block ends."""
        self.close()

    @property
    def conn(self) -> sqlite3.Connection:
        """The open connection, created together with the schema on first use."""
        if self._conn is None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(self.path)
            self._conn.execute("PRAGMA foreign_keys = ON")
            self._conn.executescript(_SCHEMA)
        return self._conn

    def close(self) -> None:
        """Close the connection, if one was ever opened."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def works(self, artist_id: int) -> list[IllustInfo] | None:
        """The listing an earlier run saved for one artist.

        Args:
            artist_id: The artist's pixiv user id.

        Returns:
            Their works, newest first, or None if no run has ever listed them
            to the end. An artist who has posted nothing gives an empty list,
            which is why the two cases are not both falsy.
        """
        cur = self.conn.execute("SELECT 1 FROM artists WHERE artist_id = ?", (artist_id,))
        if cur.fetchone() is None:
            return None
        rows = self.conn.execute(
            "SELECT illust_id, title, links FROM works WHERE artist_id = ? ORDER BY position",
            (artist_id,),
        )
        return [{"id": illust_id, "title": title, "links": json.loads(links)} for illust_id, title, links in rows]

    def save(self, artist_id: int, works: Sequence[IllustInfo]) -> None:
        """Record one artist's whole listing, replacing what was there.

        Call this only after the listing was walked to the end -- either from
        the cache or from pixiv -- since that is what the stored listing
        promises to be.

        Args:
            artist_id: The artist's pixiv user id.
            works: Their works, newest first.
        """
        with self.conn:
            self.conn.execute(
                "INSERT INTO artists (artist_id, updated_at) VALUES (?, ?)"
                " ON CONFLICT (artist_id) DO UPDATE SET updated_at = excluded.updated_at",
                (artist_id, datetime.now(tz=UTC).isoformat()),
            )
            self.conn.execute("DELETE FROM works WHERE artist_id = ?", (artist_id,))
            self.conn.executemany(
                "INSERT INTO works (artist_id, position, illust_id, title, links) VALUES (?, ?, ?, ?, ?)",
                [
                    (artist_id, position, work["id"], work["title"], json.dumps(work["links"]))
                    for position, work in enumerate(_deduplicated(works))
                ],
            )


def _deduplicated(works: Iterable[IllustInfo]) -> list[IllustInfo]:
    """Drop the works whose id was already seen, keeping the first of each.

    A listing merged out of a fresh page and the cache can name the same work
    twice; the table's primary key would refuse the second one.

    Args:
        works: The listing to clean up.

    Returns:
        The same listing without the repeats.
    """
    seen: set[int] = set()
    unique: list[IllustInfo] = []
    for work in works:
        if work["id"] in seen:
            continue
        seen.add(work["id"])
        unique.append(work)
    return unique
