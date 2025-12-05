# RealTrack Ingestion Architecture (Plain-English)

This diagram shows, step-by-step, how each RealTrack transaction moves from the website into our local files and finally into the structured data that the app will use. No coding knowledge required.

```mermaid
flowchart TD
    subgraph A[1. Scheduler]
        S(launchd timer or manual run)
        note right of S
          This simply kicks off the ingest script
          at 9am, 11am, 2pm, and 4pm.
        end note
    end

    subgraph B[2. Per Search Page]
        R[Open RealTrack results page
(skip = 0, 50, 100...)]
        E[Click "Export Page" link for the same skip
(get postal code + building size table)]
        L[Walk each row/detail in order
(row 0 matches skip, row 1 matches skip+1...)]
        D[Open the detail page
(save HTML + photos/PDFs)]
        X[Attach the export row info
(postal code, building SF, etc.)]
        U[Save everything + remember RT ID]
    end

    subgraph C[3. Local Storage]
        H[Raw HTML files
 e.g. data/raw_html/RT195679.html]
        A[Photos/PDFs + manifest
 data/raw_assets/RT195679/]
        M[Summary JSONL with
 postal codes, sizes, prices]
        I[Seen RT IDs list
(so we never re-download)]
    end

    subgraph D[4. Refinement]
        SD[Split HTML into sections
 (addresses, parties, site, etc.)]
        AN[Normalize addresses
(shared Cleo address engine)]
        PP[Parse parties (companies,
contacts, phones, addresses)]
        FO[Produce final facts
(date, price, postal, building size...)]
    end

    S --> R
    R --> E
    E --> L
    L --> D
    D --> X
    X --> U
    U --> H
    U --> A
    U --> M
    U --> I

    H --> SD
    A --> SD
    M --> FO
    SD --> AN
    SD --> PP
    AN --> FO
    PP --> FO

    I -. tells next run where to stop .-> S
```
