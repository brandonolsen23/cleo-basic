"""Helpers for extracting metadata from RealTrack search pages."""

from __future__ import annotations

import re

TOTAL_RE = re.compile(r"\.pagination\((\d+),")


def extract_total_count(html: str) -> int:
    """Return the RealTrack total result count embedded in their pagination JS."""

    match = TOTAL_RE.search(html)
    if not match:
        raise ValueError("Unable to locate total count on search page")
    return int(match.group(1))
