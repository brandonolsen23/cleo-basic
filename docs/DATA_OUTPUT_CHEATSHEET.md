# RealTrack Data Output Cheat Sheet

Plain-English map of what each script writes and where it goes.

## Scripts

- `scripts/realtrack_ingest/fetch_new_realtrack_transactions.py`
  - Log in, run the saved search, and download new transactions.
- `scripts/realtrack_ingest/reset_realtrack_data.py`
  - Delete everything the ingest script writes so you can try again from scratch.

## File locations

| Purpose | Path | Written by |
| --- | --- | --- |
| Detail HTML | `data/raw_html/realtrack/RT{ID}.html` | `fetch_new_realtrack_transactions.py` |
| Downloaded assets (images / PDFs) | `data/raw_assets/realtrack/RT{ID}/` | `fetch_new_realtrack_transactions.py` |
| Asset manifest | `data/raw_assets/realtrack/RT{ID}/manifest.json` | `fetch_new_realtrack_transactions.py` |
| Transaction ID ledger | `data/state/seen_rt_ids.json` | `fetch_new_realtrack_transactions.py` |
| Browser/session state | `data/state/realtrack_storage_state.json` | `fetch_new_realtrack_transactions.py` |
| launchd stub | `ops/launchd/com.cleo.realtrack.ingest.plist` | manually edited |
| Cleanup target directories | `data/raw_html/realtrack/`, `data/raw_assets/realtrack/`, `data/state/` | `reset_realtrack_data.py` |

Everything stays local; the reset script blanks the HTML, assets, and state directories so the ingest run can rebuild them. Use this table when you need to inspect or delete specific outputs.
