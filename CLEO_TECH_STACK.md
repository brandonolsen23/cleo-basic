# Cleo Tech Stack

All choices in this document are **final decisions**, not options.  
The goal is a **local-first**, **JSONL-first** pipeline with a thin analytical DB layer and a modern React web app.

---

## 1. High-Level Architecture

- **Ingestion & Processing:** Python 3.12
- **Scheduling:** macOS `launchd` (local cron-style jobs)
- **Primary Storage of Record:** JSONL files on disk
- **Analytical DB / Query Engine:** DuckDB (single local `.duckdb` file)
- **Backend API:** FastAPI (Python) talking to DuckDB + JSONL
- **Frontend Web App:** Next.js (React + TypeScript) with Tailwind CSS
- **Charts / Visuals:** Recharts
- **Package / build tooling:**
  - Python: `poetry`
  - Frontend: `pnpm` (or `npm` if you prefer, but we’ll assume `pnpm`)

Everything runs locally on your Mac; no Supabase, no hosted DB is required for this RealTrack/brand pipeline.

---

## 2. Languages & Core Libraries

### 2.1 Python (Ingestion + Backend + Data Processing)

- **Version:** Python 3.12
- **Dependency manager:** `poetry`

Core libs:

- **Browser automation / scraping**
  - `playwright` (Python package: `playwright`)
- **HTML parsing**
  - `beautifulsoup4`
  - `lxml` (parser backend)
- **Data wrangling**
  - `pydantic` (for typed models of Transactions, Properties, Parties)
  - `pandas` (for ad-hoc manipulations / exports)
- **Address processing**
  - Custom module: `cleo_address` (our own deterministic rules for:
    - expansion (commas, `&`, hyphen ranges)
    - normalization (suffixes, casing, whitespace)
    - canonical string + hash)
- **JSON & files**
  - `orjson` (fast JSON)
  - `pathlib` / `glob` for filesystem
- **Database / analytics**
  - `duckdb` (Python integration)
- **API backend**
  - `fastapi`
  - `uvicorn[standard]` (ASGI server)
- **Geocoding (later)**
  - `geopy` (thin wrapper; provider decided via config)

### 2.2 TypeScript / React (Frontend)

- **Framework:** Next.js 15 (App Router)
- **Language:** TypeScript
- **UI & Layout:**
  - Tailwind CSS
  - Headless UI / Radix UI (for menus, popovers, etc., if needed)
- **Data fetching & caching:**
  - `@tanstack/react-query`
- **Charts:**
  - `recharts`
- **Build tooling:**
  - `pnpm` (preferred), but project works fine with `npm` or `yarn`

---

## 3. Storage & Data Model

### 3.1 JSONL as Source of Truth

All ingestion ultimately writes to **JSONL** files under `data/`:

- `data/transactions.jsonl`
- `data/party_addresses.jsonl`
- `data/properties.jsonl` (canonical properties, built in a later step)
- `data/brand_locations.jsonl`
- `data/entities.jsonl` (normalized parties, later)
- `data/holdings.jsonl` (who owns what, later)

JSONL is the **authoritative source**.  
DuckDB is a **derived analytical layer** that can always be rebuilt from JSONL.

### 3.2 DuckDB

- Single DB file: `data/cleo.duckdb`
- Tables:
  - `transactions`
  - `party_addresses`
  - `properties`
  - `brand_locations`
  - `entities`
  - `holdings`
- Loaded / refreshed by Python scripts:
  - `scripts/load_duckdb_from_jsonl.py`
- All heavy queries in the web app (e.g. “top 50 buyers last 12 months”) hit DuckDB via FastAPI.

---

## 4. Automation & Scheduling

### 4.1 Scheduler

- **Tool:** macOS `launchd`
- **Schedule:** 4× per day (e.g. 9:00, 11:00, 14:00, 16:00 EST)
- **Job:** run a shell script that does:

```bash
cd /path/to/cleo-realtrack
poetry run python scripts/fetch_new_realtrack_transactions.py
```

The Python script:

1. Launches Playwright (headless).
2. Logs into RealTrack.
3. Navigates to the saved search (with fixed retail parameters).
4. Reads first page (skip=0), extracts RTNumbers.
5. Compares against `data/seen_rt_numbers.json`.
6. For each new RTNumber:
   - Fetches the detail page.
   - Saves raw HTML under `raw_html/RT{number}.html`.

### 4.2 Ingestion / Parsing

- **Script:** `scripts/ingest_realtrack_html.py`
- **Responsibilities:**
  - Walk `raw_html/` for new files.
  - Extract sections with BeautifulSoup.
  - Parse into Pydantic models (Transaction, Party, Site, etc.).
  - Run address expansion + normalization via `cleo_address`.
  - Append structured records into `data/transactions.jsonl` and `data/party_addresses.jsonl`.
  - Optionally trigger `load_duckdb_from_jsonl.py` at the end (or on a separate schedule).

---

## 5. Address Normalization / Hashing (Shared Between RealTrack & Brands)

### 5.1 Shared Python Module: `cleo_address`

All address handling (RealTrack and brand feeds) goes through the same module.

- **Module path:** `cleo_address/`
- **Key functions:**
  - `expand_subject_address_block(raw_lines) -> list[str]`
  - `normalize_address_string(addr: str) -> NormalizedAddress`
  - `canonical_str(normalized: NormalizedAddress) -> str`
  - `address_hash(canonical_str) -> str` (e.g. SHA-256)

**NormalizedAddress (Pydantic):**

```python
class NormalizedAddress(BaseModel):
    street_number: str
    street_name: str
    street_suffix: str
    municipality: str | None = None
    region: str | None = None
    province: str | None = "ON"
    postcode: str | None = None
    country: str = "Canada"
```

### 5.2 Expansion Rules (Subject Property Lines)

- Split on commas and ampersands to get number tokens.
- For hyphen ranges like `556 - 560`, keep endpoints only (`556` and `560`).
- Attach shared street name/suffix once.
- Deduplicate within a single transaction’s `AllParsed` list.

### 5.3 Normalization Rules (Shared with Brand Addresses)

- Uppercase all text.
- Collapse multiple spaces to one.
- Standardize suffixes (documented in `cleo_address/suffix_map.py`):
  - `DRIVE, DR.` → `DR`
  - `ROAD, RD.` → `RD`
  - `AVENUE, AVE.` → `AVE`
  - `STREET, ST.` → `ST`
  - etc.
- Strip punctuation noise (commas where not needed, trailing periods).
- Strip unit separators like `UNIT`, `STE`, `SUITE` into a `street_number` or separate unit field.
- Normalize Canadian postal codes to `A1A 1A1` format.
- Build canonical string:

```text
{STREET_NUMBER} {STREET_NAME} {SUFFIX}, {MUNICIPALITY}, {PROVINCE} {POSTCODE}
```

Fields are omitted if missing, but ordering is always consistent.

### 5.4 Hashing

- Hash: `SHA256(canonical_string)`.
- Hex digest becomes `address_hash`.
- Used as stable join key when building `properties.jsonl`.
- Brand ingestion must import and call the exact same functions from `cleo_address`. No re-implementation.

---

## 6. Backend API (FastAPI)

- **App path:** `backend/main.py`
- **Responsibilities:**
  - Open `cleo.duckdb` and expose read-only query endpoints such as:
    - `/transactions/recent`
    - `/entities/{id}/portfolio`
    - `/analytics/volume`
    - `/properties/search`
  - Optionally expose low-level debug endpoints over JSONL for internal use.
- **Auth:** local dev only to start (no auth). Later add simple token or basic auth if needed.

---

## 7. Frontend (Next.js + Tailwind)

- **Directory:** `frontend/`
- Fetches data exclusively from FastAPI.
- Uses React Server Components for heavy views.
- Uses React Query on the client for interactive / filtered views.
- **Visualizations:** Recharts for:
  - time-series of transaction volume / value,
  - party transaction histories,
  - portfolio breakdowns.

---

## 8. Summary

- Python 3.12 + Playwright + BeautifulSoup handle RealTrack login, scraping, parsing.
- JSONL is the ground truth for transactions, parties, properties, brands.
- DuckDB provides fast local analytics, queried via FastAPI.
- Next.js + TypeScript + Tailwind + Recharts render the Cleo dashboard.
- `cleo_address` is the single source of logic for:
  - subject address expansion,
  - RealTrack address normalization,
  - brand address normalization,
  - canonical string & hashing.

This satisfies:

- Local-only, no Supabase dependency.
- Deterministic address matching between RealTrack and brand feeds.
- A clean, testable ingestion and analytics pipeline.
