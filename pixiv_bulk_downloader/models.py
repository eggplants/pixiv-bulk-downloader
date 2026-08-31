"""Shapes of the metadata collected before anything is downloaded."""

from __future__ import annotations

from typing import TypedDict


class IllustInfo(TypedDict):
    """One illustration and the original-size URL of each of its pages."""

    id: int
    title: str
    links: list[str]


class ArtistInfo(TypedDict):
    """A followed artist and every illustration they have posted."""

    id: int
    name: str
    account: str
    illusts: list[IllustInfo]
