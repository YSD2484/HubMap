# Environment Setup & Getting Started

This repository provides the full stack of the HubMap platform: database initialization, ML pipelines, and the web interface.

## 1. System Pre-Requisites
1. **Docker**: Required to run the PostgreSQL database with the `pgvector` extension locally.
2. **Conda Environment**: Required for the ML pipeline. The environment (`vela313`) uses Python 3.13 and includes dependencies like XGBoost, Gensim, Pydantic, and Optuna.
3. **Node/npm**: Required for the React + Vite frontend environment.

## 2. Infrastructure & Database Initialization
Ensure your local Docker daemon is running, and initialize the database:
```bash
sudo docker-compose up -d
```
*Note: This generates the `vela-postgres` container binding port `5432`.*

Variables are loaded via `core/config.py` from the `.env` file. Ensure `FOUNDER_DATA_BQ_CREDENTIALS` points to the correctly provisioned `.json` credential map for BigQuery extraction.

## 3. Full Pipeline Execution
To execute the entirely integrated system end-to-end—spanning BigQuery extraction, entity matching, embedding generation, XGBoost training, and model evaluation—run the unified pipeline runner:

```bash
./run_pipeline.sh
```

## 4. Web Stack Startup
To boot the backend and frontend simultaneously for dashboard inspection:

```bash
./start.sh
```
This script dynamically:
1. Uses `uvicorn` to run the `backend.app:app` API endpoints on Port `8000`.
2. Initiates the Vite environment via `npm run dev`, mapped locally to Port `3000`.

## 5. Sub-Script Sandboxing
To run partial pipeline stages manually without triggering XGBoost Optuna grids, use the conda shell directly:
```bash
/home/ysd2484/miniconda3/envs/vela313/bin/python scripts/ingest_data.py
```
