"""Command line entry point for fetching new RealTrack transactions."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Set

from dotenv import load_dotenv

from cleo_realtrack.ingest import (
    RealTrackSession,
    ensure_absolute,
    extract_detail_links,
    extract_rt_id,
    extract_total_count,
    prepare_saved_search,
    open_saved_search,
    SearchConfig,
    verify_html_vs_state,
    verify_known_rt_encounter,
    verify_total_count_bounds,
    download_transaction_assets,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
RAW_HTML_DIR = DATA_DIR / "raw_html" / "realtrack"
RAW_ASSETS_DIR = DATA_DIR / "raw_assets" / "realtrack"
STATE_DIR = DATA_DIR / "state"
SEEN_IDS_FILE = STATE_DIR / "seen_rt_ids.json"
STORAGE_STATE_FILE = STATE_DIR / "realtrack_storage_state.json"

load_dotenv(REPO_ROOT / ".env")


def load_seen_ids() -> Set[str]:
    if not SEEN_IDS_FILE.exists():
        return set()
    data = json.loads(SEEN_IDS_FILE.read_text())
    return set(data)


def save_seen_ids(seen: Set[str]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    SEEN_IDS_FILE.write_text(json.dumps(sorted(seen)))


def save_detail_html(rt_id: str, html: str) -> Path:
    RAW_HTML_DIR.mkdir(parents=True, exist_ok=True)
    output_path = RAW_HTML_DIR / f"{rt_id}.html"
    if output_path.exists():
        raise RuntimeError(f"Refusing to overwrite existing HTML for {rt_id}")
    output_path.write_text(html)
    return output_path


def build_search_config() -> SearchConfig:
    start_year = os.environ.get("REALTRACK_SEARCH_START_YEAR") or SearchConfig().start_year
    end_year_env = os.environ.get("REALTRACK_SEARCH_END_YEAR")
    return SearchConfig(start_year=start_year, end_year=end_year_env or None)


async def fetch_new_transactions() -> None:
    seen_ids = load_seen_ids()
    initial_seen_count = len(seen_ids)

    RAW_HTML_DIR.mkdir(parents=True, exist_ok=True)
    verify_html_vs_state(RAW_HTML_DIR, seen_ids)

    username = os.environ.get("REALTRACK_USERNAME")
    password = os.environ.get("REALTRACK_PASSWORD")
    if not username or not password:
        raise RuntimeError("REALTRACK_USERNAME and REALTRACK_PASSWORD must be set in .env")

    max_pages = int(os.environ.get("REALTRACK_MAX_PAGES", "1"))
    if max_pages < 1:
        raise RuntimeError("REALTRACK_MAX_PAGES must be >= 1")

    new_rt_ids: list[str] = []
    found_known = False
    search_config = build_search_config()

    async with RealTrackSession(
        storage_state_path=STORAGE_STATE_FILE,
        username=username,
        password=password,
    ) as session:
        await session.ensure_login()

        first_page_html = await prepare_saved_search(session, search_config)

        for page_index in range(max_pages):
            if page_index == 0:
                search_html = first_page_html
            else:
                search_html = await open_saved_search(session, page_index=page_index)
            if page_index == 0:
                total_count = extract_total_count(search_html)
                verify_total_count_bounds(total_count, seen_ids)
            links = extract_detail_links(search_html)
            absolute_links = ensure_absolute(session.base_url, links)

            for detail_link in absolute_links:
                detail_html = await session.fetch(detail_link)
                rt_id = extract_rt_id(detail_html)

                if rt_id in seen_ids:
                    found_known = True
                    break

                save_detail_html(rt_id, detail_html)
                seen_ids.add(rt_id)
                new_rt_ids.append(rt_id)
                await download_transaction_assets(
                    session=session,
                    rt_id=rt_id,
                    html=detail_html,
                    assets_root=RAW_ASSETS_DIR,
                )

            if found_known:
                break

    if initial_seen_count > 0:
        verify_known_rt_encounter(found_known)

    if new_rt_ids:
        print(f"Saved {len(new_rt_ids)} new RealTrack transactions")
    else:
        print("No new RealTrack transactions detected")

    save_seen_ids(seen_ids)
    verify_html_vs_state(RAW_HTML_DIR, seen_ids)


def main() -> None:
    asyncio.run(fetch_new_transactions())


if __name__ == "__main__":
    main()
