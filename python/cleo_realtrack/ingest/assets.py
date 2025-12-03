"""Asset extraction and downloading for RealTrack detail pages."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List
from urllib.parse import urlparse
import re

from bs4 import BeautifulSoup

ASSET_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".pdf")
WINDOW_OPEN_RE = re.compile(r"window\.open\(\s*['\"]([^'\"]+)['\"]")


@dataclass
class AssetRecord:
    filename: str
    source_url: str


def extract_asset_urls(html: str) -> List[str]:
    """Return ordered, deduplicated asset links from a RealTrack detail page."""

    soup = BeautifulSoup(html, "lxml")
    raw_links: list[str] = []

    for anchor in soup.find_all("a"):
        href = (anchor.get("href") or "").strip()
        onclick = (anchor.get("onclick") or "").strip()
        rel = anchor.get("rel") or []

        js_match = WINDOW_OPEN_RE.search(onclick)
        js_url = js_match.group(1) if js_match else None

        candidate_url = href if href and href != "#" else None
        lower_href = (candidate_url or "").lower()
        lower_js = (js_url or "").lower()

        should_capture = False
        if any(str(value).lower().startswith("shadowbox") for value in rel):
            should_capture = True
        elif candidate_url and lower_href.endswith(ASSET_EXTENSIONS):
            should_capture = True
        elif js_url and lower_js.endswith(ASSET_EXTENSIONS):
            should_capture = True

        if not should_capture:
            continue

        asset_url = candidate_url or js_url
        if not asset_url:
            continue

        raw_links.append(asset_url)

    deduped: list[str] = []
    seen: set[str] = set()
    for href in raw_links:
        if href in seen:
            continue
        seen.add(href)
        deduped.append(href)

    for img in soup.find_all("img", src=True):
        src = img["src"].strip()
        if not src:
            continue
        lower_src = src.lower()
        if not lower_src.endswith(ASSET_EXTENSIONS) and "realtrack" not in lower_src:
            continue
        if src in seen:
            continue
        seen.add(src)
        deduped.append(src)
    return deduped


def _pick_filename(url: str, asset_dir: Path, fallback_prefix: str) -> str:
    parsed = urlparse(url)
    candidate = Path(parsed.path).name or f"{fallback_prefix}.bin"
    filename = candidate
    counter = 1
    while (asset_dir / filename).exists():
        stem = Path(candidate).stem or fallback_prefix
        suffix = Path(candidate).suffix or ".bin"
        filename = f"{stem}_{counter}{suffix}"
        counter += 1
    return filename


async def download_transaction_assets(
    session,
    rt_id: str,
    html: str,
    assets_root: Path,
) -> list[AssetRecord]:
    """Download referenced assets for the given RealTrack transaction."""

    urls = extract_asset_urls(html)
    if not urls:
        return []

    asset_dir = assets_root / rt_id
    asset_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = asset_dir / "manifest.json"

    manifest: list[AssetRecord] = []
    if manifest_path.exists():
        data = json.loads(manifest_path.read_text())
        for item in data.get("assets", []):
            manifest.append(AssetRecord(**item))

    existing_sources = {record.source_url for record in manifest}

    for index, url in enumerate(urls, start=1):
        absolute_url = session.build_url(url)
        if absolute_url in existing_sources:
            continue

        filename = _pick_filename(absolute_url, asset_dir, f"{rt_id}_{index}")
        content = await session.download_binary(absolute_url)
        (asset_dir / filename).write_bytes(content)

        record = AssetRecord(filename=filename, source_url=absolute_url)
        manifest.append(record)
        existing_sources.add(absolute_url)

    manifest_payload = {
        "rt_id": rt_id,
        "assets": [record.__dict__ for record in manifest],
    }
    manifest_path.write_text(json.dumps(manifest_payload, indent=2))
    return manifest
