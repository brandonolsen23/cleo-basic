"""RT ID extraction helpers."""

from __future__ import annotations

import re
from typing import Optional

RT_ID_RE = re.compile(r"RT(\d{5,})")


def extract_rt_id(html: str) -> str:
    """Extract the first RT identifier from a RealTrack detail page."""

    match = RT_ID_RE.search(html)
    if not match:
        raise ValueError("Could not find RT ID in HTML payload")
    return f"RT{match.group(1)}"


def try_extract_rt_id(html: str) -> Optional[str]:
    """Gracefully return None when the HTML does not contain an RT ID."""

    match = RT_ID_RE.search(html)
    if not match:
        return None
    return f"RT{match.group(1)}"
