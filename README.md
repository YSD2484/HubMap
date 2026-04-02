# HubMap Founder Prediction Platform

Welcome to the HubMap Founder Network Data Pipeline and UI. This project provides backend infrastructure, a machine learning pipeline, and an interactive properties dashboard designed to predict the probability of success for startup founders, based on their socio-educational and professional networks.

The system hypothesizes that the networks and specific overlapping hubs (such as universities and previous employers) a founder participates in correlate with their future probability of securing high-tier capital or building successful companies.

## High-Level Architecture

The platform architecture spans three primary environments:

1. **Data Ingestion & Graph Backend (Postgres & SQL)**
   We extract batch data from BigQuery, normalize entities, and construct a unipartite founder-to-founder graph. 
   The system utilizes an extensive feature space evaluating localized embeddings alongside standard network structural centralities (PageRank, Coreness, Betweenness).

2. **Predictive Machine Learning Pipeline (XGBoost LTR)**
   Deep temporal embeddings are computed via chronological properties bounding network elements. These are combined with organizational "Mafia" hubs and relational network success distributions into a Pooled Ranker Model (`XGBRanker`). Model performance is evaluated using Out-Of-Sample (OOS) testing intervals mapped beyond historical target cutoffs.

3. **Inference Backend & Interactive Dashboard (FastAPI & React/Vite)**
   A FastAPI system operates parameter lookups for real-time `SHAP` values, computing local Subnetwork subsets and topography models programmatically evaluated within a Vite-based UI interface. The UI features a dedicated Admin Console to explore multiplier relationships across structural features.

---

## Documentation Directory

The `docs/` directory has been updated to provide explicit technical explanations mapping specific project nodes.

### Core Getting Started
- **[Getting Started](docs/getting_started.md)**: Container setup instructions, execution scripts, and environment variable standards.
- **[Data Ingestion](docs/data_ingestion.md)**: Logic covering pipeline extractions, try/except boundaries, Postgres UPSERT definitions, and Pydantic object mappings.

### Architecture & Schemas
- **[Database Schema](docs/database_schema.md)**: Covers explicit schema layouts linking `Founders`, `Companies`, `Schools`, relational sets (`Jobs`, `Educations`), and array cluster subsets (`Hubs`).
- **[Machine Learning Pipeline](docs/ml_pipeline.md)**: Deep breakdown of Graph matrix limits, point-in-time restrictions, Node Embeddings (`Word2Vec`), XGBoost categorical implementations, and LTR empirical evaluation constraints.
- **[Frontend & API Architecture](docs/frontend_and_api.md)**: FastAPI deployment variables, React component mappings, context logic, and Top-level state parameters.

### Reference
- **[Dependencies & LLM Utilities](docs/utilities_and_llms.md)**: Review of how the system parses strings across `gpt-4o-mini` boundaries cleanly alongside string verification protocols.
- **[HubMap Founder Data README](docs/FOUNDERDATAREADME.md)**: Details the internal `founder-data` type-safe package parsing objects explicitly from standard BigQuery output queries.

---

## Quick Run

With the Docker configuration active and the `vela313` environment sourced properly:

Run the unified data and ML process directly:
```bash
./run_pipeline.sh
```

Boot the frontend React server alongside the FastAPI backend endpoints simultaneously:
```bash
./start.sh
```
