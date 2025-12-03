# RealTrack Ingest Engine (Ingestion Only, With Safety Checks)

This document defines the **ingestion layer only** for RealTrack:

- Logs into RealTrack  
- Applies fixed search parameters  
- Walks newest transactions (skip=0,1,2…)  
- Detects which RT IDs are NEW  
- Saves the detail HTML for each new RT  
- Updates `seen_rt_ids.json`  

It does **not** parse HTML, normalize addresses, geocode, or build JSONL.  
Those functions belong to the *refinement engine*.

This version **adds critical safety mechanisms** ensuring data integrity.

---

# 1. Responsibilities of the Ingest Engine

### It *must*:
- Log into RealTrack (via Playwright + stored session)
- Navigate to the fixed retail search
- Read skip=0 results (newest 50)
- Continue with skip=1, skip=2… until the first **known** RT ID
- Save new HTML detail pages untouched
- Maintain a perfect state file (`seen_rt_ids.json`)

### It *must NOT*:
- Parse HTML into structured JSON
- Normalize addresses
- Geocode addresses
- Update DuckDB

---

# 2. Directory & State Layout

```
cleo/
  scripts/
    fetch_new_realtrack_transactions.py

  data/
    raw_html/
      realtrack/
        RT195679.html
        RT195680.html
        ...

    state/
      seen_rt_ids.json
      realtrack_storage_state.json
```

---

# 3. External Inputs & Outputs

### Inputs
- RealTrack credentials (`REALTRACK_USERNAME`, `REALTRACK_PASSWORD`)
- `seen_rt_ids.json` (optional on first run)
- `realtrack_storage_state.json` (optional on first run)

### Outputs
- New HTML files under `data/raw_html/realtrack/`
- Updated `seen_rt_ids.json`

---

# 4. Core RealTrack Invariants Used by the Engine

These are **guaranteed rules** your ingest engine depends on:

1. **Sort = Newest First** always  
2. **skip=0** is always **newest transaction**  
3. Detail pages always contain an **RT ID** (e.g., `RT195679`)  
4. RT IDs are **globally unique and stable**  
5. RealTrack results JS contains the **total count** of all matching transactions  
6. You never expect more than ~50 new transactions between run intervals  

---

# 5. High‑Level Algorithm

```
load seen_rt_ids.json → seen_rt_ids (set)

start Playwright
load storage_state if available
else login, then save storage_state

open RealTrack standard search with fixed parameters

extract total_count from RealTrack JavaScript (critical validity check)

found_known_rt = False
new_rt_ids = []

for page_index in [0, 1, 2, 3]:
    go to that skip page
    extract detail links

    for each detail page:
        extract RT ID
        if RT ID in seen_rt_ids:
            found_known_rt = True
            break out of loops

        save detail HTML
        new_rt_ids.append(rt)
        seen_rt_ids.add(rt)

if not found_known_rt:
    raise "Ordering invariant broken: expected known RT by skip <= 3"

write updated seen_rt_ids.json
run integrity checks
exit
```

---

# 6. Extracting Detail Links

Use Playwright locator scanning & URL filtering.

```
<a href="/ici_comps_details?ID=xxxxx">
```

Filter only detail links. Deduplicate while preserving order.

---

# 7. Extracting RT IDs

Use regex on full HTML:

```
r"RT(\d+)"
```

Return `"RT{digits}"`.

Fail the run if no RT ID found.

---

# 8. Saving New Detail HTML

Every new RT ID writes a file:

```
data/raw_html/realtrack/RT{ID}.html
```

Never overwrite an existing file.

---

# 9. State Management: seen_rt_ids.json

Format:

```json
["RT195679", "RT195680", ...]
```

On update:

```python
SEEN_RT_FILE.write_text(json.dumps(sorted(seen_rt_ids)))
```

---

# 10. Pagination Handling

Iterate pages: **skip = 0, 1, 2, 3**

Stop immediately when encountering the first previously seen RT ID.

If no known RT is encountered by skip=3 → **invariant broken**.

---

# 11. ⚠️ CRITICAL SAFETY CHECKS  
These protect against silent data corruption.

## **Check 1: HTML Files Count Must Match seen_rt_ids Count**

After saving new HTML:

```python
html_files = list(RAW_DIR.glob("RT*.html"))
if len(html_files) != len(seen_rt_ids):
    raise Exception("Mismatch: HTML files count != seen_rt_ids count")
```

Prevents:
- partial runs
- accidental deletions
- corrupted state

---

## **Check 2: RealTrack JS Total Count Must Be ≥ len(seen_rt_ids)**

Extract from search page:

```js
.pagination(15503,
```

Regex:

```python
TOTAL_RE = re.compile(r"\.pagination\((\d+),")
total_rt_count = int(TOTAL_RE.search(page.content()).group(1))
```

Then:

```python
if len(seen_rt_ids) > total_rt_count:
    raise Exception("seen_rt_ids exceeds RealTrack total count — corruption detected")

if total_rt_count - len(seen_rt_ids) > 100:
    raise Exception("Unexpectedly huge 'new transactions' gap — RealTrack likely changed UI")
```

---

## **Check 3: You Must Encounter a Known RT by skip ≤ 3**

If not:

```
raise Exception("Ordering invariant broken: expected to find known RT by skip<=3")
```

This tests:

- sort order  
- search settings  
- RealTrack UI integrity  
- your saved state integrity  

---

# 12. Error Behavior

The ingest script should:

- Print errors clearly  
- Refuse to continue when *any* invariant breaks  
- Never try to “auto repair” data silently  

Broken integrity should **stop ingestion immediately**.

---

# 13. Relationship to the Refinement Engine

This ingest layer **only** creates:

- a complete set of guaranteed-correct HTML files  
- a growing list of RT IDs in chronological order  

The refinement layer handles:

- HTML parsing  
- Pydantic modeling  
- expansion / normalization / hashing  
- geocoding  
- promotion to JSONL and DuckDB  

---

# 14. Summary

The RealTrack Ingest Engine is a **minimal, deterministic, safety‑checked** component that guarantees:

- Only newest RT transactions are downloaded  
- Never duplicates  
- Never missing files  
- RealTrack ordering assumptions are validated each run  
- Total RT universe size is always coherent  
- Raw HTML is always complete and correctly indexed  

It is the **foundation** of the reliability of your entire Cleo dataset.
