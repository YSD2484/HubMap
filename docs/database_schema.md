# Postgres Database Schema Overview

The predictive platform relies upon a relational **PostgreSQL** schema mapped via SQLAlchemy ORM (`core/db.py`). The database uses the `pgvector` extension and Docker containers for deployment.

## Primary Entity Nodes

### 1. `Founders`
- **Definition**: The central atomic unit representing individual founders. Operations and networks are mapped relative to these points.
- **Constraints**: Relies on a UUID Primary Key (`id`), with standard string definitions for names.

### 2. `Companies` & `Schools`
- **Definition**: The secondary layer of nodes representing organizations and educational institutions.
- **Constraints**: Both encode a string logic boundary via `normalized_name`. Using `utils/utils.py`, organization names are lower-cased and stripped of non-alphanumeric characters to handle variation across extraction APIs.
- **Indexing**: `normalized_name` is encoded with a unique constraint to prevent duplicate organizational nodes.

## Bipartite Relational Edges

### 3. `Jobs`
- **Definition**: Many-to-Many relationship table connecting `Founders` to `Companies`.
- **Chronology**: Incorporates specific `start_year` and `end_year` logic to support temporal graph embeddings and prevent leakage of future associations during point-in-time constraints.
- **Integrity**: Enforces an explicit `UniqueConstraint('founder_id', 'company_id', 'role', 'start_year')`. Ingestions via PostgreSQL `ON CONFLICT DO NOTHING` safely bypass duplicate records.

### 4. `Educations`
- **Definition**: Many-to-Many bounding `Founders` to `Schools` utilizing chronological boundaries (`start_year`, `end_year`).
- **Integrity**: Explicit `UniqueConstraint('founder_id', 'school_id', 'degree', 'start_year')`.

## Pre-Aggregated Structural Topography

### 5. `Hubs`
- **Definition**: A database view tracking groups of founders. Because Python-oriented group operations can be slow over millions of relational edges, `Hubs` acts as a materialized layer mapping physical organization nodes to arrays of affiliated founders.
- **Construction**: Maps a generic `hub_id` UUID and a string marker (`company` or `school`) against an `ARRAY of UUIDs`.
- **Merge Logic**: Bounded by `UniqueConstraint('hub_type', 'hub_id')`. When batch extracting new records, ingestion executes an `INSERT ... ON CONFLICT DO UPDATE` query to append missing IDs to the `founder_ids` arrays.
