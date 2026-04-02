# Common Utilities & LLM Integration

The predictive platform requires unstructured dataset consolidation. This directory contains scripts related to string standardization, generic utilities, and Language Model (LLM) processing.

## 1. LLM Client Orchestration (`core/llm_clients.py`)

Entity resolution and physical organization scaling often rely on data formats that are difficult to process via traditional deterministic scraping. LLM wrappers are employed for edge-case definitions.

- `openai_client`: Instantiates secure completions based on the `OPENAI_API_KEY` configuration.
- **Model Choice**: Operations map across `gpt-4o-mini`. Due to the volume of parsing needed for string-diff matching (`resolve_entities.py`) and numerical context querying (`get_hub_sizes.py`), this model provides cost-effective throughput for structured JSON parsing via Pydantic constructs.

## 2. General Data Transform Utilities (`utils/utils.py`)
Standard optimization functions used across the ingestion framework.

- `normalize_string(s)`: Lowers case and extracts basic `[a-z0-9]` sequences. Forms the foundational structure for PostgreSQL `normalized_name` string lookups, mitigating standard capitalization or whitespace differentials.
- `match_strings`: Execution wrapper extending `rapidfuzz` string metrics.
- `normalize_date(d_obj, fallback)`: The point-in-time constraints depend upon accurate chronologies. This function isolates string and format variables securely mapping inputs to `pd.Timestamp` output values.
- `google_search` / `number_to_money`: Basic string formatters bounding parameter variables.

## 3. Profile Entity Extractors (`utils/profile_helpers.py`)
Consolidates distinct array logic for unstructured APIs.
- Because `FounderProfile` structures arrays dynamically across multiple unformatted inputs, `profile_helpers` limits structural errors.
- Typical functions isolated here include `extract_company_name`, `extract_school_name`, and nested dictionary parsing boundaries.
