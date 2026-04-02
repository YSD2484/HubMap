# Batch Data Ingestion

The platform integrates directly with the `founder-data` BigQuery wrapper to load records into the PostgreSQL layer.

## Process Flow Structure & Resiliency

### 1. The Pydantic Extractor (`founder_data`)
- The pipeline initiates synchronously via `load_founder_profiles()`.
- Leveraging `pydantic` object logic, JSON structures are mapped into typed Python architectures (`FounderProfile`). 
- **Caching**: The generator writes to `.feather` files to limit redundant API requests.

### 2. Pipeline Execution (`scripts/ingest_data.py`)
- **Fault-Tolerance**: `process_single_founder()` handles node extraction inside a `try...except` wrapper. If errors occur (e.g., malformed dates or missing fields), the specific Founder transaction is rolled-back without halting the broader batch execution.
- **Relational Integrity**: Entities iterate over the `utils.profile_helpers` extractors—identifying node dimensions bounded to PG via `ON CONFLICT DO NOTHING` statements.

### 3. Materialization via UPSERT
- The `generate_hubs()` step targets Postgres SQL directly with an `INSERT ... ON CONFLICT DO UPDATE` operation. It instructs the DB to merge string arrays (`EXCLUDED.founder_ids`) into overlapping `founder_ids`, significantly reducing performance overhead compared to full rebuilds.

### 4. Entity Disambiguation (`scripts/resolve_entities.py`)
Unstructured scraping produces string fragmentation (e.g., "Y Combinator" vs "Y-Combinator LLC"). This script manages entity consolidation.
- **Algorithmic Sub-pass**: Implements `rapidfuzz` string metrics to cluster high-correlation thresholds.
- **LLM Consensus Engine**: Passes candidate node arrays across LLM instances (`gpt-4o-mini`). If the consensus resolves that distinct strings map to a unified corporate definition, the IDs are consolidated.
- PostgreSQL subsequently updates across `Jobs` relationships, re-mapping associations to the unified UUID.
