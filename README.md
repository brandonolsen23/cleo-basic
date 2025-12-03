# Cleo Basic

Bootstrap of the Cleo local-first data stack focused on the RealTrack ingest pipeline.

## Environment setup

1. Copy `.env.example` to `.env` and provide your RealTrack credentials (local only). Leave `REALTRACK_MAX_PAGES=1` while you test first-page runs.
2. Install dependencies with `poetry install`.
3. Run `poetry run playwright install` once so Chromium is available for the ingest script.

## Quick iteration loop

- Run `poetry run python scripts/realtrack_ingest/fetch_new_realtrack_transactions.py` to grab up to `REALTRACK_MAX_PAGES × 50` transactions (defaults to 50). Each transaction now saves:
  - Detail HTML under `data/raw_html/realtrack/`
  - Any linked photos / PDFs under `data/raw_assets/realtrack/{RTID}/`
  - `manifest.json` next to the assets so downstream code knows which files belong to which RT
- If anything fails, reset the ingest outputs with `poetry run python scripts/realtrack_ingest/reset_realtrack_data.py`, fix the issue, then rerun. The reset script wipes HTML, assets, and state files so you start from scratch.
