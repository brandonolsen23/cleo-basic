"""Utilities for finding RealTrack detail links on the search page."""

from __future__ import annotations

import re
from typing import Iterable, List

DETAIL_LINK_RE = re.compile(r'href="([^"]*?page=details[^"]*)"')


def extract_detail_links(html: str) -> List[str]:
    """Return ordered, deduplicated detail links from a snippet of HTML."""

    matches = [match.replace("&amp;", "&") for match in DETAIL_LINK_RE.findall(html)]
    seen: set[str] = set()
    ordered: list[str] = []
    for link in matches:
        if link in seen:
            continue
        seen.add(link)
        ordered.append(link)
    return ordered


def ensure_absolute(base_url: str, links: Iterable[str]) -> List[str]:
    """Prefix relative links with the RealTrack base URL."""

    normalized: list[str] = []
    for link in links:
        if link.startswith("http"):
            normalized.append(link)
            continue
        if link.startswith("?"):
            normalized.append(f"{base_url.rstrip('/')}/{link}")
        elif link.startswith("/"):
            normalized.append(f"{base_url.rstrip('/')}{link}")
        else:
            normalized.append(f"{base_url.rstrip('/')}/{link}")
    return normalized
