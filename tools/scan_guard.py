"""The source checkers' guard: a scan that read nothing found nothing wrong.

A checker given the wrong root, or a directory renamed under it, reads zero
files and passes. Each checker names the file its rule is about (its owner);
unscanned() is a problem unless that file was among those read.
"""

from __future__ import annotations

from pathlib import Path


def unscanned(root: Path, scanned: list[str], owner: str) -> list[str]:
    """[] when `owner` (a path relative to root) is in `scanned`, else the problem to report."""
    if owner in scanned:
        return []
    return [f"{owner} was not scanned ({len(scanned)} files read under {root}); "
            "is that the repository root?"]
