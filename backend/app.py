"""
backend/app.py
--------------
FastAPI backend for the Vela Founder Prediction Dashboard.

Exposes four REST endpoints:
    GET /api/search      — Founder name search by substring.
    GET /api/predict     — SHAP-explained outlier probability for a single founder.
    GET /api/graph       — 1st + 2nd degree ego-graph subnetwork for a founder.
    GET /api/topography  — Full ecosystem scatter plot data (PageRank vs. Capital vs.
                           Degree Centrality).
    GET /api/leaderboard — Top founders ranked by specific metrics.

All endpoints are backed by a shared in-memory ``CACHE`` keyed on ``t_anchor``. The
first request for a given anchor triggers a full data load + model train cycle;
subsequent requests are served instantly from cache.

Note on model:
    The backend trains a fresh XGBoost classifier on every first load for that anchor.
    This provides live SHAP explainability but is not the same model as the pre-trained
    ``xgb_pooled_model.json`` SuperModel. For production use, consider loading the
    pre-trained model and calling ``XGBRanker.predict()`` directly.
"""

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import xgboost as xgb
import shap
import os

app = FastAPI(title="Vela Founder Backend")

# Allow CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global caches
CACHE = {}

def get_db_session():
    from core.db import get_session
    return get_session()

def load_data(t_anchor: str = "2024-01-01"):
    """Load the feature matrix, train an XGBoost model, and cache everything.

    On first call for a given ``t_anchor``, this function:
        1. Reads ``data/feature_matrix_{t_anchor}.feather``.
        2. Calls ``extract_future_outcome`` to get Valuation Waterfall scores
           at ``t_anchor + 5 years``.
        3. Labels the global top-15% as y=1 via ``label_outlier``.
        4. Trains an XGBoost classifier for SHAP explainability.
        5. Loads the weighted graph edges and founder name map.
        6. Stores all results in the ``CACHE`` dict.

    Subsequent calls for the same anchor return the cached object immediately.

    Args:
        t_anchor (str): Anchor date in ``YYYY-MM-DD`` format.

    Returns:
        dict: Cache entry with keys: ``df``, ``features``, ``model``,
              ``explainer``, ``edges``, ``id_to_name``.

    Raises:
        HTTPException 404: If the feature matrix file does not exist.
    """
    if t_anchor in CACHE:
        return CACHE[t_anchor]
        
    feat_path = f"data/feature_matrix_{t_anchor}.feather"
    if not os.path.exists(feat_path):
        raise HTTPException(status_code=404, detail="Feature matrix not found for this anchor date")
        
    df = pd.read_feather(feat_path)
    df['id'] = df['id'].astype(str)
    
    # Compute the Valuation Waterfall targets at t_anchor + 5 years
    from utils.ml_utils import label_outlier
    outcome_df = pd.read_feather(f"data/y_target_{t_anchor}.feather")
    df = df.merge(outcome_df, on='id', how='left')
    df['future_outcome'] = df['future_outcome'].fillna(0)
    
    # Global top-15% labeling (no cohort binning)
    df['y'] = label_outlier(df)
    
    drop_cols = ['id', 'future_outcome', 'most_recent_role', 'most_recent_degree', 'y']
    features = [c for c in df.columns if c not in drop_cols]
    
    categorical_cols = ['primary_mafia_id', 'louvain_community_id']
    for col in categorical_cols:
        if col in df.columns:
            df[col] = df[col].astype('category')
            
    X = df[features]
    y = df['y']
    
    # Train full XGBoost model for SHAP and predicting
    model = xgb.XGBClassifier(
        objective='binary:logistic',
        eval_metric='aucpr',
        scale_pos_weight=19,
        max_depth=3,
        learning_rate=0.02,
        subsample=0.95,
        colsample_bytree=0.6,
        gamma=3.9,
        n_estimators=150,
        random_state=42,
        enable_categorical=True
    )
    model.fit(X, y, verbose=False)
    
    # Explainer
    explainer = shap.TreeExplainer(model)
    
    # Edges
    edges_path = f"data/weighted_graph_{t_anchor}.feather"
    edges_df = pd.read_feather(edges_path) if os.path.exists(edges_path) else None
    
    # Founder Name Map
    from core.db import Founder
    session = get_db_session()
    founders = session.query(Founder.id, Founder.name).all()
    id_to_name = {str(f.id): f.name for f in founders}
    session.close()

    CACHE[t_anchor] = {
        'df': df,
        'features': features,
        'model': model,
        'explainer': explainer,
        'edges': edges_df,
        'id_to_name': id_to_name
    }
    return CACHE[t_anchor]

@app.get("/api/search")
def search_founders(q: str = Query(..., min_length=2), t_anchor: str = "2024-01-01"):
    """Search for founders by name substring.

    Returns up to 10 founders whose names contain the query string (case-insensitive).

    Args:
        q (str): Search string (minimum 2 characters).
        t_anchor (str): Anchor date to load data for. Defaults to ``2024-01-01``.

    Returns:
        dict: ``{ results: [ { id, name }, ... ] }``
    """
    try:
        data = load_data(t_anchor)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    df = data['df']
    id_to_name = data['id_to_name']
    
    results = []
    q_lower = q.lower()
    for fid in df['id'].unique():
        name = id_to_name.get(fid, "Unknown")
        if q_lower in name.lower():
            results.append({"id": fid, "name": name})
            if len(results) >= 10:
                break
    return {"results": results}

@app.get("/api/predict")
def predict_founder(founder_id: str, t_anchor: str = "2024-01-01"):
    """Get the outlier prediction score and SHAP waterfall for a single founder.

    Loads the cached model for the given anchor, runs inference on the founder's
    feature row, and returns the top 15 SHAP contributors grouped into two
    interpretability buckets: *Network Structure* (embeddings, centrality) and
    *Historical Milestones* (capital raised, senior roles).

    Args:
        founder_id (str): UUID string of the founder.
        t_anchor (str): Anchor date used to select the feature/model cache.

    Returns:
        dict: Contains ``founder_id``, ``name``, ``prediction_score_percentile``,
              ``stats``, ``shap_base_value``, and ``shap_waterfall`` (top 15 drivers).

    Raises:
        HTTPException 404: If the founder is not in the feature matrix.
    """
    data = load_data(t_anchor)
    df = data['df']
    
    row = df[df['id'] == founder_id]
    if len(row) == 0:
        raise HTTPException(status_code=404, detail="Founder not found in feature matrix")
        
    X_single = row[data['features']]
    
    # Inference
    prob = float(data['model'].predict_proba(X_single)[0, 1])
    
    # SHAP
    shap_vals = data['explainer'].shap_values(X_single)[0]
    base_val = float(data['explainer'].expected_value)
    
    # Group SHAP into structural (embeddings, network) vs tabular (capital, roles)
    shap_breakdown = []
    for i, feat in enumerate(data['features']):
        val = X_single.iloc[0, i]
        try:
            # SHAP breakdown needs float values for the UI charts
            f_val = float(val) if not isinstance(val, str) else 0.0
        except (ValueError, TypeError):
            f_val = 0.0

        shap_breakdown.append({
            "feature": feat,
            "value": f_val,
            "shap": float(shap_vals[i]),
            "type": "Network Structure" if feat.startswith("emb_") or feat in ['pagerank', 'degree_centrality'] else "Historical Milestones"
        })
        
    shap_breakdown.sort(key=lambda x: abs(x['shap']), reverse=True)
    
    return {
        "founder_id": founder_id,
        "name": data['id_to_name'].get(founder_id, "Unknown"),
        "prediction_score_percentile": round(prob * 100, 2),
        "stats": {
            "prior_raised": float(row['prior_amount_raised_usd'].iloc[0]),
            "prior_roles": int(row['prior_senior_roles'].iloc[0]),
            "years_of_experience": float(row.get('years_of_experience', pd.Series([0.0])).iloc[0]),
            "career_velocity": float(row.get('career_velocity', pd.Series([0.0])).iloc[0]),
            "serial_founder_count": int(row.get('serial_founder_count', pd.Series([0])).iloc[0]),
            "pagerank": float(row['pagerank'].iloc[0]),
            "degree_centrality": float(row['degree_centrality'].iloc[0]),
            "betweenness_centrality": float(row.get('betweenness_centrality', pd.Series([0.0])).iloc[0]),
            "coreness": float(row.get('coreness', pd.Series([0.0])).iloc[0]),
            "louvain_community_id": str(row.get('louvain_community_id', pd.Series(["none"])).iloc[0]),
            "primary_mafia_id": str(row.get('primary_mafia_id', pd.Series(["none"])).iloc[0]),
            "degree_assortativity": float(row.get('degree_assortativity', pd.Series([0.0])).iloc[0]),
            "neighborhood_success_rate": float(row.get('neighborhood_success_rate', pd.Series([0.0])).iloc[0])
        },
        "shap_base_value": base_val,
        "shap_waterfall": shap_breakdown[:15]  # Top 15 drivers
    }

@app.get("/api/graph")
def get_ego_graph(founder_id: str, t_anchor: str = "2024-01-01"):
    """Return the 1st and 2nd degree ego-graph subnetwork for a founder.

    Finds all founders directly connected to ``founder_id`` (1st degree), then
    computes the subgraph induced by those neighbors (2nd degree edges). 
    To prevent browser-crashing O(N^2) edge explosions, we cap 1st-degree 
    neighbors at the top 40 most relevant (highest weighted) connections.

    Args:
        founder_id (str): UUID of the focal founder.
        t_anchor (str): Anchor date to select the graph snapshot.

    Returns:
        dict: ``{ nodes: [...], edges: [...], capped: bool }``
    """
    data = load_data(t_anchor)
    edges_df = data['edges']
    id_to_name = data['id_to_name']
    
    if edges_df is None:
        return {"nodes": [], "edges": [], "capped": False}
        
    # Find 1st degree
    e1_out = edges_df[edges_df['u'] == founder_id]
    e1_in = edges_df[edges_df['v'] == founder_id]
    e1 = pd.concat([e1_out, e1_in]).drop_duplicates()
    
    # Sort by weight and cap to prevent memory crashes on the frontend
    # If the user has thousands of neighbors, N^2 edges = 1M+ edges.
    e1 = e1.sort_values('weight', ascending=False)
    is_capped = len(e1) > 40
    e1_capped = e1.head(40)
    
    # Extract unique neighbors (including ego)
    neighbors_1 = set(e1_capped['u']).union(set(e1_capped['v']))
    
    # Find 2nd degree edges ONLY within this tightly bounded subnetwork
    e2 = edges_df[(edges_df['u'].isin(neighbors_1)) & (edges_df['v'].isin(neighbors_1))]
    
    nodes_set = set(e2['u']).union(set(e2['v'])).union(neighbors_1)
    
    nodes = [{"id": n, "label": id_to_name.get(n, "Unknown"), "group": "ego" if n == founder_id else "neighbor"} for n in nodes_set]
    edges = [{"source": r['u'], "target": r['v'], "weight": float(r['weight']), "hub": r['hub'], "type": r['hub_type']} for _, r in e2.iterrows()]
    
    return {"nodes": nodes, "edges": edges, "capped": is_capped}

@app.get("/api/topography")
def get_topography(t_anchor: str = "2024-01-01"):
    """Return scatter plot coordinates for all founders at the given anchor.

    Each point corresponds to one founder and is positioned by:
        - ``x``: PageRank (network centrality)
        - ``y``: Prior amount raised (capital access)
        - ``z``: Degree centrality (direct connections)

    Intended for the ecosystem topography scatter map in the dashboard.

    Args:
        t_anchor (str): Anchor date to select the data snapshot.

    Returns:
        dict: ``{ points: [ { id, x, y, z }, ... ] }``
    """
    data = load_data(t_anchor)
    df = data['df'].copy()
    
    # Ensure binning exists for coloring/cohorting in the UI
    if 'net_bin' not in df.columns:
        df['net_bin'] = pd.qcut(df['pagerank'].rank(method='first'), q=5, labels=False, duplicates='drop')
    if 'cap_bin' not in df.columns:
        df['cap_bin'] = pd.qcut(df['prior_amount_raised_usd'].rank(method='first'), q=5, labels=False, duplicates='drop')

    points = []
    # Sample down if too large, but 4k should be fine for a scatter plot
    for _, row in df.iterrows():
        points.append({
            "id": row['id'],
            "x": float(row['pagerank']),
            "y": float(row['prior_amount_raised_usd']),
            "z": float(row['degree_centrality']),
            "cohort": f"{int(row['net_bin'])+1}_{int(row['cap_bin'])+1}"
        })
        
    return {"points": points}

@app.get("/api/admin/metrics")
def get_admin_metrics(t_anchor: str = "2024-01-01"):
    """Return 'likelihood multipliers' (lifts) for continuous features and Mafia IDs.
    
    Returns the top Mafias (count >= 5) and key continuous features (top 20% tier)
    showing how much more likely success is relative to the global baseline.
    
    Args:
        t_anchor (str): Anchor date to select the data snapshot.
        
    Returns:
        dict: { mafia_lifts: [...], feature_lifts: [...] }
    """
    data = load_data(t_anchor)
    df = data['df']
    
    global_success_rate = df['y'].mean()
    if global_success_rate == 0:
        return {"mafia_lifts": [], "feature_lifts": [], "global_rate": 0}
        
    # Mafia Lifts
    mafia_df = df[df['primary_mafia_id'] != 'none'].copy()
    mafia_stats = mafia_df.groupby('primary_mafia_id').agg(
        founder_count=('id', 'count'),
        successes=('y', 'sum')
    ).reset_index()
    
    mafia_stats['success_rate'] = mafia_stats['successes'] / mafia_stats['founder_count']
    mafia_stats['multiplier'] = mafia_stats['success_rate'] / global_success_rate
    
    valid_mafias = mafia_stats[mafia_stats['founder_count'] >= 5]
    top_mafias = valid_mafias.sort_values('multiplier', ascending=False).head(20)
    
    mafia_lifts = []
    for _, row in top_mafias.iterrows():
        mafia_lifts.append({
            "id": row['primary_mafia_id'],
            "count": int(row['founder_count']),
            "success_rate": float(row['success_rate']),
            "multiplier": float(row['multiplier'])
        })
        
    # Feature Lifts
    target_features = [
        ('pagerank', 'High PageRank (Top 20%)'),
        ('prior_amount_raised_usd', 'High Capital (Top 20%)'),
        ('prior_senior_roles', 'High Experience (Top 20%)'),
        ('degree_centrality', 'High Subnetwork degree (Top 20%)'),
        ('coreness', 'High Coreness (Top 20%)'),
        ('neighborhood_success_rate', 'High Neighborhood Success (Top 20%)'),
        ('betweenness_centrality', 'High Betweenness (Top 20%)')
    ]
    
    feature_lifts = []
    for col, display_name in target_features:
        if col not in df.columns:
            continue
            
        threshold = df[col].quantile(0.80)
        # Using >= threshold
        top_tier = df[df[col] >= threshold]
        count = len(top_tier)
        if count == 0:
            continue
            
        rate = top_tier['y'].mean()
        mult = rate / global_success_rate
        
        feature_lifts.append({
            "feature": display_name,
            "threshold": float(threshold),
            "success_rate": float(rate),
            "multiplier": float(mult)
        })
        
    feature_lifts.sort(key=lambda x: x['multiplier'], reverse=True)
        
    return {
        "global_rate": float(global_success_rate),
        "mafia_lifts": mafia_lifts,
        "feature_lifts": feature_lifts
    }

@app.get("/api/leaderboard")
def get_leaderboard(
    t_anchor: str = "2024-01-01",
    metric: str = Query("score", enum=["score", "pagerank", "capital", "degree", "neighborhood_success"]),
    limit: int = Query(20, ge=1, le=100)
):
    """Return top N founders ranked by the specified metric.

    Supported metrics:
        - score: Outlier probability (y_prob)
        - pagerank: Network centrality
        - capital: Prior amount raised
        - degree: Direct network connections
        - neighborhood_success: VC Alpha (neighbors' success rate)

    Args:
        t_anchor (str): Anchor date for data segment.
        metric (str): Ranking criteria.
        limit (int): Number of results (max 100).

    Returns:
        dict: { results: [ { rank, id, name, value }, ... ] }
    """
    data = load_data(t_anchor)
    df = data['df'].copy()
    
    # Map friendly metric names to columns
    metric_map = {
        "score": "y_prob",
        "pagerank": "pagerank",
        "capital": "prior_amount_raised_usd",
        "degree": "degree_centrality",
        "neighborhood_success": "neighborhood_success_rate"
    }
    
    col = metric_map[metric]
    
    # If metric is score, we need to compute it for everyone if it doesn't exist
    if metric == "score" and "y_prob" not in df.columns:
        X = df[data['features']]
        df['y_prob'] = data['model'].predict_proba(X)[:, 1]
    
    top_df = df.sort_values(col, ascending=False).head(limit)
    id_to_name = data['id_to_name']
    
    results = []
    for i, (_, row) in enumerate(top_df.iterrows()):
        results.append({
            "rank": i + 1,
            "id": row['id'],
            "name": id_to_name.get(row['id'], "Unknown"),
            "value": float(row[col])
        })
        
    return {"results": results}
