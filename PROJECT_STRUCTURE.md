# Cleo Project Structure

This document defines the recommended monorepo layout for the Cleo data platform, covering:
- RealTrack ingestion
- Brand scrapers
- Unified refinement pipeline
- Address normalization engine
- JSONL + DuckDB storage model
- API backend
- Frontend web app
- Tests, ops, and documentation

---

# 1. Top-Level Structure

```
cleo/
  apps/
    api/                
    web/                

  python/
    cleo_core/          
    cleo_address/       
    cleo_realtrack/     
    cleo_brands/        
    cleo_refinement/    
    cleo_analysis/      

  data/
    raw_html/
      realtrack/
      brands/
    raw_feeds/
      brands/
    jsonl/
      transactions.jsonl
      party_addresses.jsonl
      properties.jsonl
      brand_locations.jsonl
      entities.jsonl
      holdings.jsonl
    duckdb/
      cleo.duckdb
    state/
      seen_rt_ids.json
      realtrack_storage_state.json
      brand_tim_hortons_state.json

  scripts/
    realtrack_ingest/
    brand_ingest/
    refinement/
    analysis/

  docs/
  ops/
  tests/

  pyproject.toml
  package.json
  README.md
```

---

# 2. Python Package Breakdown

## `python/cleo_core/`
Shared foundational modules:

```
models/
  transactions.py
  properties.py
  brands.py
  entities.py
  holdings.py
utils/
  jsonl_io.py
  logging_utils.py
settings.py
```

This holds canonical Pydantic models.

---

## `python/cleo_address/`
Single source of truth for address processing:

```
models.py
normalize.py
expand.py
hash.py
suffix_map.py
postal_code.py
tests/
```

All address handling (RealTrack + brands) must use these functions.

---

## `python/cleo_realtrack/`
RealTrack-specific ingest and helpers:

```
ingest/
  login.py
  search_nav.py
  extract_links.py
  extract_rt_id.py
  integrity_checks.py
  cli_fetch_new.py
parse/
  blocks.py
  subject_block.py
  party_block.py
  site_block.py
  consideration_block.py
  photos_block.py
```

Divide ingest (raw HTML only) from parsing (refinement engine).

---

## `python/cleo_brands/`
Brand scrapers:

```
tim_hortons/
  scrape.py
  parse_raw.py
sobeys/
  scrape.py
  parse_raw.py
...
```

Outputs pre-normalized brand location rows for refinement.

---

## `python/cleo_refinement/`
The unified transformation engine:

```
realtrack_pipeline.py
brand_pipeline.py
address_pipeline.py
geocode_pipeline.py
promote_to_jsonl.py
promote_to_duckdb.py

cli/
  refine_realtrack.py
  refine_brands.py
  rebuild_duckdb.py
```

This takes raw RealTrack HTML or brand feeds → normalized JSONL → DuckDB.

---

## `python/cleo_analysis/`
Analytics helpers:

```
queries.py
reports.py
charts.py
```

The API and app will often call into these.

---

# 3. Data Layout (`data/`)

```
data/
  raw_html/
    realtrack/
    brands/
  raw_feeds/
    brands/
  jsonl/
    transactions.jsonl
    party_addresses.jsonl
    properties.jsonl
    brand_locations.jsonl
    entities.jsonl
    holdings.jsonl
  duckdb/
    cleo.duckdb
  state/
    seen_rt_ids.json
    realtrack_storage_state.json
    brand_tim_hortons_state.json
```

**Raw → refined JSONL → DuckDB**  
DuckDB is always fully reconstructible.

---

# 4. Scripts Layer (`scripts/`)

```
scripts/
  realtrack_ingest/
    fetch_new_realtrack_transactions.py
  brand_ingest/
    fetch_tim_hortons.py
    fetch_sobeys.py
  refinement/
    refine_realtrack.py
    refine_brands.py
    rebuild_duckdb.py
  analysis/
    dump_top_buyers.py
    generate_weekly_report.py
```

Scripts are thin wrappers around Python package functions.

---

# 5. Web App Layer (`apps/`)

## `apps/api/` (FastAPI)

```
app/
  main.py
  deps.py
  routers/
    transactions.py
    properties.py
    entities.py
    analytics.py
tests/
pyproject.toml
```

Connects to DuckDB and exposes query endpoints.

---

## `apps/web/` (Next.js)

```
app/
  page.tsx
  transactions/
  properties/
  buyers/
  analytics/
components/
  charts/
  tables/
  filters/
lib/
  api-client.ts
public/
package.json
tailwind.config.js
tsconfig.json
```

The UI for interacting with transactions, properties, parties, analytics.

---

# 6. Documentation (`docs/`)

```
docs/
  CLEO_DATA_STACK.md
  REALTRACK_INGEST_ENGINE.md
  REALTRACK_INGESTION_PROCESS.md
  REALTRACK_CONSTANTS.md
  REALTRACK_TECH_STACK.md
  BRAND_INGESTION_GUIDE.md
  ADDRESS_NORMALIZATION.md        (future)
  DATA_MODEL.md                   (future)
  PIPELINE_OVERVIEW.md            (future)
```

Central reference for all architectural decisions.

---

# 7. Ops (`ops/`)

```
ops/
  launchd/
    com.cleo.realtrack.ingest.plist
    com.cleo.refinement.realtrack.plist
  config/
    .env.example
    settings.local.template.toml
```

Automation + deployment-related assets.

---

# 8. Tests (`tests/`)

```
tests/
  unit/
    test_cleo_address.py
    test_realtrack_ingest_integrity.py
    test_realtrack_parsers.py
  integration/
    test_realtrack_pipeline.py
    test_brand_pipeline.py
  fixtures/
    realtrack_detail_*.html
    brand_tim_hortons_sample.json
```

Consistent and stable regression safety.

---

# 9. Summary

This structure provides:

- **Clear separation of ingest vs refinement**
- **Shared address engine across RealTrack + brands**
- **Unified JSONL data model**
- **Composable pipelines**
- **Local-first, DuckDB-powered analytics**
- **A clean monorepo for the Next.js app + FastAPI backend**
- **Scalability** as more brands, pipelines, and analytic features are added

You can drop this directly into your repository as `PROJECT_STRUCTURE.md`.
