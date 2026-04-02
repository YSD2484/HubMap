# Machine Learning Pipeline Architecture

The HubMap Founder prediction platform relies on chronologically structured pipelines. These processes transform raw relational Postgres entities into point-in-time compliant graph embeddings, and ultimately feed Gradient Boosted architectures.

Below is a breakdown of how the ML pipeline generates predictions and mitigates target leakage.

## 1. Temporal Graph Extraction (`scripts/build_graph.py`)
Founder profiles are loaded through asynchronous batches. Graph structures require edge definitions between Founders (nodes). 
- We execute a unipartite mathematical transform. Two founders share an undirected edge if they intersect at a shared "Hub" (a `Company` or `School`). 
- **Point in Time (PiT) constraint**: To prevent future bias, every edge is tagged structurally with a specific historical timestamp defined by the duration of the affiliation (`started_on` and `ended_on`). An intersection is algorithmically valid only if their tenures genuinely overlap.

## 2. Dynamic Algorithmic Edge Weighting (`scripts/query_graph.py` & `scripts/get_hub_sizes.py`)
Predictions define a Point-in-Time target termed $t_{anchor}$. Edges are subjected to continuous transformations evaluated precisely at $t_{anchor}$.

- **Context Sizes**: We utilize `scripts/get_hub_sizes.py` to fetch organization sizes ($S_h$). Connecting at a small startup implies a stronger social tie than connecting at a major corporation. The platform dynamically scopes employee and academic scale.
- **Transformation**: Edges are weighted by intersection duration ($O_{u,v,h}$), scaled inversely by the size of the hub ($\log_b(S_h)$), and exponentially decayed based on the gap between the end of the affiliation and $t_{anchor}$.

## 3. Topographical Vector Mappings (`scripts/train_embeddings.py`)
- We initiate randomized iterative traversals (Random Walks/DeepWalk) originating from every founder profile within the network.
- Crucially, the walker is strictly chronologically constrained. A probabilistic step from Hub A to Hub B is only valid if the chronological tenure overlap of B initiates subsequent to or concurrently with the start of A.
- Traversals are encoded via Gensim's **Word2Vec (Skip-Gram with Negative Sampling)** into robust 64-Dimensional numerical dense vectors representing structural positioning.

## 4. Feature Space Concatenation (`scripts/assemble_features.py`)
`assemble_features.py` unifies variables precisely calculated relative to $t_{anchor}$. 
- Incorporates **80+ features** across network and career modalities:
  - **Structural Centrality**: PageRank, Eigenvector, Betweenness ($O(V^3)$ sampled), Closeness, Coreness ($k$-shell), Clustering Coefficient, and Degree Assortativity.
  - **Temporal Communities**: Louvain community detection assigns founders to historical network clusters.
  - **Historical "Mafias"**: Categorical identifiers tracking tenure at specific top-tier organizations within rolling 3-year windows (e.g. `google_2004_2006`).
  - **"VC Alpha" (Neighborhood Success Rate)**: Measures the percentage of a founder's 1st-degree neighbors who had achieved outlier success prior to $t_{anchor}$.
  - **Profile Velocity**: Years of experience, senior role count, and longitudinal career velocity.
- Appends localized `Word2Vec` graph embeddings.
- Handles categorical features (Mafias, Communities) via native categorical encoding in XGBoost.

### 5. Historical Analysis Case Study ($N=5,000$)
A sample analysis run conducted across 5,000 founders and 83 features generated the following parameters.

**Feature Significance:**
| Rank | Variable | Impact Factor |
|---|---|---|
| 1 | `prior_amount_raised_usd` | Standard Baseline |
| 2 | `degree_centrality` | Degree of Direct Connectivity |
| 3 | **`coreness`** | Network Core Indicator |
| 4 | **`neighborhood_success_rate`** | Social Capital Metric |
| 5 | **`betweenness`** | Information Graph Brokerage |

## 6. Learning-to-Rank with XGBoost (`scripts/train_pooled_model.py`)
To isolate predictive signals across class imbalances, we employ a **Learning-to-Rank (LTR-Pairwise)** algorithm.
- **Valuation Waterfall Target**: Success is defined via a priority waterfall measured at $t_{anchor} + 5$ years: `IPO` -> `M&A` -> `Post-Money Valuation` -> `Imputed Valuation` (5x capital raised).
- **Global Labeling**: Within each anchor slice, the upper 15% of founders by outcome value are categorized as categorical outliers.
- **XGBRanker (Super Model)**: We merge feature matrices from multi-year historical anchors into a single array block. The model optimizes a `rank:pairwise` LTR objective with `NDCG` parameters, computing ordered relationships across founders internal to each year group.
- **Hyperparameter Optimization**: Stratified cross-validation is tuned with Optuna.

## 7. Out of Sample Testing (`scripts/evaluate_model.py`)
Testing mimics true production usage constraints.
- Evaluation runs force a continuous 5-year chronological barrier separating the Training target variable evaluation from out-of-sample data distributions. 
- Discretized sub-cohorts (e.g., "$3M raised cohort") rely upon defined cutoff constraints mapped strictly from training validation distributions—preventing evaluation leakage.

## 8. Likelihood Multiplier Analysis (Lift Diagnostic)
The platform evaluates feature impacts via "Likelihood Multipliers" (Lifts). This metric quantifies the divergence between specific attribute cohorts and global baseline success metrics.
- **Feature Lifts**: Evaluates the success rate within the top continuous distribution quintile (top 20%) relative to the global metric.
- **Mafia Lifts**: Investigates local organization success density. Tracks the performance multiplier of individuals engaging with specific organizational hubs dynamically across corresponding temporal limits.
- Metrics are tracked via `/api/admin/metrics` and visible within the Admin interfaces.
