# RealTrack Ingestion Architecture (Plain-English)

This diagram shows, step-by-step, how each RealTrack transaction moves from the website into our local files and finally into the structured data that the app will use. No coding knowledge required. The scheduler node simply means "launchd or a manual CLI run kicks off the ingest around 9am, 11am, 2pm, and 4pm".

```mermaid
flowchart TD
    subgraph A[1. Scheduler]
        S[launchd timer or manual run]
    end

    subgraph B[2. Per Search Page]
        R["Open results page skip=0/50/100"]
        E["Click Export Page for same skip"]
        L["Walk each row/detail in order"]
        D["Open detail page, save HTML + photos"]
        X["Attach export row extras"]
        U["Save files + remember RT ID"]
    end

    subgraph C[3. Local Storage]
        H["Raw HTML files data/raw_html/..."]
        A["Photos/PDFs + manifest data/raw_assets/..."]
        M["Summary JSONL postal codes, sizes, prices"]
        I["Seen RT IDs list prevents re-downloads"]
    end

    subgraph D[4. Refinement]
        SD["Split HTML into sections"]
        AN["Normalize addresses"]
        PP["Parse parties companies/contacts/phones"]
        FO["Produce final facts date/price/postal/size"]
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
