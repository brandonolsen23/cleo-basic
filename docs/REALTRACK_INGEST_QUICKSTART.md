# RealTrack Ingest Quickstart

Plain-English checklist for running and retrying the RealTrack scraper.

## 1. One-time prep

1. Install dependencies: `poetry install`
2. Download Playwright browsers: `poetry run playwright install`
3. Copy `.env.example` → `.env`
4. Fill in the two lines in `.env`:
   - `REALTRACK_USERNAME=...`
   - `REALTRACK_PASSWORD=...`
   Leave `REALTRACK_MAX_PAGES=1` so only the newest 50 deals are touched while testing.

## 2. Run the scraper

```bash
poetry run python scripts/realtrack_ingest/fetch_new_realtrack_transactions.py
```

What the script does:

- Logs in with the `.env` credentials
- Runs the saved retail search
- Visits up to `REALTRACK_MAX_PAGES × 50` detail pages (default: 50)
- Saves each new detail page as `data/raw_html/realtrack/RTxxxxxx.html`
- Downloads every linked photo/PDF into `data/raw_assets/realtrack/{RTID}/`
- Updates `data/state/seen_rt_ids.json` so we know what has been downloaded

The script stops the moment it hits an already-downloaded RT number to guard against RealTrack changing the sort order.

## 3. Reset between attempts

If the run fails or you just want to try again from scratch:

```bash
poetry run python scripts/realtrack_ingest/reset_realtrack_data.py
```

This removes:

- Every file under `data/raw_html/realtrack/`
- Every file under `data/raw_assets/realtrack/`
- `data/state/seen_rt_ids.json`
- `data/state/realtrack_storage_state.json`

After resetting, simply rerun the fetch command.

## 4. Expanding beyond the first 50

When you are confident in the run, bump the page count in `.env`:

```
REALTRACK_MAX_PAGES=4
```

Each page is 50 transactions, so `4` means the newest ~200 deals before the “first known RT ID” rule halts the run. Lower it back to `1` any time you need a quick smoke test.

## 5. Where things land

- Raw HTML: `data/raw_html/realtrack/*.html` (source of truth for detail pages)
- Asset bundles: `data/raw_assets/realtrack/{RTID}/` + `manifest.json`
- State: `data/state/seen_rt_ids.json` (all RT IDs we’ve fetched so far)
- Browser session cookies: `data/state/realtrack_storage_state.json`

## 6. Optional scheduling

When you want macOS to run the ingest automatically, follow `docs/LAUNCHD_SETUP.md`. The bundled plist runs the scraper at 9:00, 11:00, 14:00, and 16:00 EST, and you can load/unload it with a couple of `launchctl` commands.

These files stay local; delete them with the reset script whenever you need to restart the ingest cycle.
