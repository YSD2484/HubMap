# HubMap Dashboard Platform (Frontend)

This directory houses the highly interactive, React + TypeScript web application serving the HubMap predictive metrics. It is orchestrated tightly with **Vite** for instantaneous Hot Module Replacements (HMR) and optimized build bundles.

## Core Features & Interface
- **Ego-Graph Physics Constraints**: Natively iterates chronological `react-force-graph-2d` network pathways tracking founders and the specific, overlapping corporate/academic entity definitions (Hubs).
- **Localized SHAP Distributions**: Deciphers mathematically *why* an XGBoost model predicted an outlier path. SHAP waterfalls break down explicit baseline variance into Network expectations versus independent Capital accumulation expectations seamlessly.
- **Topographical Visualization**: Scatter-maps multi-dimensional PageRank and Centrality limits against explicitly raised private-market capital using localized `recharts` primitives.

## Technology Stack
- **React 18**: The fundamental UI engine bounding functional components seamlessly via modular generic Hooks (`useState`, `useEffect`).
- **Tailwind CSS**: Utility-first boundary frameworks handling incredibly complex, multi-layered color blending, dynamic gradient stops, and real-time hover shadows cleanly outside standard HTML class trees.
- **Lucide React**: Extremely high quality SVG icon primitives.

## Local Development Initialization
To iterate on component design or edit React architectures without compiling, simply spin up the native dashboard module natively.

Before beginning, ensure your terminal spans the `frontend/` directory logically:
```bash
cd frontend
```

### 1. Install Library Matrices
Ensure you install the explicit React/Tailwind Node packages configured within standard `package.json` boundaries:
```bash
npm install
```

### 2. Initiate Local HMR Client
Execute the core Vite dev server. It operates immediately locally, and automatically reflects deep internal CSS adjustments mapping out of the UI tree instantly:
```bash
npm run dev
```

The application mounts locally via: `http://localhost:3000`.
*(Ensure the companion `FastAPI` instance resides on `http://localhost:8000` to prevent strictly typed network CORS or extraction timeout barriers.)*
