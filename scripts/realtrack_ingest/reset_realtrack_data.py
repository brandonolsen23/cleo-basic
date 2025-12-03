"""Utility to wipe RealTrack ingest outputs for a clean retry."""

from __future__ import annotations

import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
RAW_HTML_DIR = DATA_DIR / "raw_html" / "realtrack"
RAW_ASSETS_DIR = DATA_DIR / "raw_assets" / "realtrack"
STATE_DIR = DATA_DIR / "state"
STATE_FILES = [
    STATE_DIR / "seen_rt_ids.json",
    STATE_DIR / "realtrack_storage_state.json",
]


def wipe_raw_html() -> None:
    if RAW_HTML_DIR.exists():
        shutil.rmtree(RAW_HTML_DIR)
    RAW_HTML_DIR.mkdir(parents=True, exist_ok=True)


def wipe_assets() -> None:
    if RAW_ASSETS_DIR.exists():
        shutil.rmtree(RAW_ASSETS_DIR)
    RAW_ASSETS_DIR.mkdir(parents=True, exist_ok=True)


def wipe_state_files() -> None:
    for file in STATE_FILES:
        if file.exists():
            file.unlink()


def main() -> None:
    wipe_raw_html()
    wipe_assets()
    wipe_state_files()
    print("RealTrack raw HTML, assets, and state files removed. Ready for a clean run.")


if __name__ == "__main__":
    main()
