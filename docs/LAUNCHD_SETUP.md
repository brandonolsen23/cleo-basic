# Scheduling RealTrack Ingest with launchd

This job is pre-configured but **not** loaded. Follow these steps when you are ready to let macOS run the scraper automatically at **9:00, 11:00, 14:00, and 16:00 EST**.

## 1. Install the plist

```bash
mkdir -p ~/Library/LaunchAgents
cp ops/launchd/com.cleo.realtrack.ingest.plist ~/Library/LaunchAgents/
```

## 2. Load (turn on)

```bash
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.cleo.realtrack.ingest.plist
launchctl enable gui/$(id -u)/com.cleo.realtrack.ingest
```

## 3. Check status

```bash
launchctl list | grep com.cleo.realtrack.ingest
tail -f ~/Library/Logs/cleo-realtrack-ingest.log
```

## 4. Disable / unload

```bash
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.cleo.realtrack.ingest.plist
launchctl disable gui/$(id -u)/com.cleo.realtrack.ingest
```

The plist already contains the four daily run times and points at `poetry run python scripts/realtrack_ingest/fetch_new_realtrack_transactions.py`. You only need to load or unload it when you want the automation on or off.
