# Frontend & API Architecture

The HubMap platform provides a fully integrated architectural stack mapping quantitative analytics to a visual output based upon the PostgreSQL and graph parameters defined through the backend ingestion flow.

## 1. Inference Engine (`backend/app.py`)
The backend is driven by the **FastAPI** web framework natively integrated with Pydantic for input validation.

### Key Details
- **In-Memory Caching**: Upon initialization, the API instances store relevant array parameters (`feature_matrix_YYYY-MM-DD.feather`), associated graph maps (`weighted_graph_YYYY-MM-DD.feather`), and required node-name dictionaries in application memory to support rapid lookup execution.
- **XGBoost & SHAP Output**: The application initializes an instance of XGBoost alongside corresponding parameters, facilitating inference execution and computing `SHAP` values to quantify predictive attribution parameters defined internally within the request body.

### Critical Endpoints
- **`/api/search`**: An autocomplete target supporting string queries to identify founder UUIDs.
- **`/api/predict`**: The core execution parameter limit. Requires a node UUID. Computes an outlier probability `.predict_proba()` against stored arrays and maps a relative list of variables via a local `SHAP` execution to generate localized waterfall definitions.
- **`/api/graph`**: Processes point interactions. Executes $1^{st}$ and $2^{nd}$ degree edge iterations mapped directly onto graph rendering arrays, filtering out parameters outside the specified target constraints to reduce network payload overhead.
- **`/api/topography`**: Defines scatter mappings for dataset subsets tracking distributions between PageRank structure, historic capital, and Eigenvector metrics.
- **`/api/leaderboard`**: Returns sorted founder subsets grouped by specific parameter limits (e.g., PageRank ranks, expected values).
- **`/api/admin/metrics`**: Processes quantitative multiplier distributions determining the comparative probabilistic baseline differences for cohorts within specific network parameter limits or affiliated organizational hubs.

## 2. Interactive Dashboard Structure (`frontend/`)
The web application is structured upon the **React + Vite** library map alongside TypeScript language definitions (`types.ts`). Visual parameters are built heavily upon **Tailwind CSS**.

### Top-Level Structural Layout
- **Global Context (`App.tsx`)**: Central UI state definitions are parameterized within higher order component bounds. Component update flows execute sequentially reacting to `activeFounder` limits and the chosen $t_{anchor}$ period mapped across playback modules.
- **Styling (`index.css`)**: Implements base primitive imports and manages continuous variables targeting CSS configurations internally bounded within standard Vite distributions.

### Local Analytics Widgets (`src/components/`)
1. **`ShapWaterfall`**: Displays feature impact rankings representing value deviations internal to local predictions. Positives push outlier probability sequentially higher, negatives drag below baseline expectations.
2. **`EgoGraph`**: Utilizes the `react-force-graph-2d` interface executing canvas-drawn definitions rendering network elements with structural force dynamics boundaries.
3. **`AlphaScorecard`**: Organizes scalar and cohort probabilities across component definitions.
4. **`TopographyMap`**: Employs `Recharts` scatter charts defining graph boundary plots for system subsets dynamically constrained across multiple dataset arrays.
5. **`AdminConsole`**: Admin utility mapping global probabilities against corresponding cohort multiplier parameters defined through internal sub-component definitions representing feature ranges and organizational groupings.
6. **`Leaderboard`**: Component managing sorted table distributions parameterizing network subset nodes by value definitions. Supports table-to-node action events affecting the broader `activeFounder` context execution.
