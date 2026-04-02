"""
scripts/query_graph.py
----------------------
Applies Point-in-Time filtering and edge weighting to the raw graph edges.

Takes the full ``data/graph_edges.feather`` edge list produced by ``build_graph.py``
and produces a temporally filtered, weighted multigraph for a specific anchor date.
The weighting formula penalizes connections through large hubs (which are less
statistically informative) and decays associations that ended long before ``t_anchor``.

Weight formula (per edge)::

    weight = (overlap_days / log_{b_h}(hub_size)) * exp(-lambda * days_since_end)

Where:
    - ``overlap_days``   : calendar overlap between the two founders at this hub
    - ``hub_size``       : number of founders passing through this hub
    - ``b_h``            : base for the log scaling per hub type (company/school)
    - ``lambda``         : temporal decay constant (default: 0.001)
    - ``days_since_end`` : how long ago the shared tenure ended relative to t_anchor

The output preserves individual (u, v, hub, hub_type, t_h, weight) records as a
multigraph so that ``train_embeddings.py`` can perform chronological random walks.

Usage::
    python scripts/query_graph.py --t-anchor YYYY-MM-DD [--b-company 3.0] [--b-school 10.0] [--lambda 0.001]
"""

import argparse
import math
import pandas as pd


def query_graph(t_anchor_str, b_company, b_school, lambda_decay):
    """Filter and weight the raw graph edges for a given Point-in-Time anchor.

    Steps:
        1. Load ``data/graph_edges.feather`` and ``data/hub_sizes.csv``.
        2. Drop all edges whose ``overlap_start`` is strictly after ``t_anchor``.
        3. Clip ``overlap_end`` to ``t_anchor`` (closing ongoing associations at the anchor).
        4. Compute ``O_days`` (effective overlap duration in calendar days).
        5. Compute the edge weight using the hub-size-penalized temporal decay formula.
        6. Save the resulting weighted multigraph to ``data/weighted_graph_{t_anchor_str}.feather``.

    Args:
        t_anchor_str (str): Anchor date in ``YYYY-MM-DD`` format.
        b_company (float): Logarithm base for company hub size scaling. A higher value
            means large companies are penalized less. Recommended: 3.0.
        b_school (float): Logarithm base for school hub size scaling. Universities are
            typically larger than companies, so a higher base reduces their penalty.
            Recommended: 10.0.
        lambda_decay (float): Decay rate for the temporal decay factor. A larger value
            causes older associations to fade more aggressively. Recommended: 0.001.
    """
    try:
        t_anchor = pd.to_datetime(t_anchor_str).normalize()
    except Exception:
        print("Invalid t_anchor format. Use YYYY-MM-DD.")
        return

    print("Loading graph edges from data/graph_edges.feather...")
    edges_df = pd.read_feather("data/graph_edges.feather")
    
    # Enforce datetime type
    edges_df['overlap_start'] = pd.to_datetime(edges_df['overlap_start']).dt.normalize()
    edges_df['overlap_end'] = pd.to_datetime(edges_df['overlap_end']).dt.normalize()
    
    print("Loading hub sizes from data/hub_sizes.csv...")
    try:
        hub_sizes_df = pd.read_csv("data/hub_sizes.csv")
    except Exception:
        print("data/hub_sizes.csv not found! Run get_hub_sizes.py first.")
        return
        
    hub_sizes = {}
    for _, row in hub_sizes_df.iterrows():
        hub_sizes[(row['hub'], row['hub_type'])] = float(row['size'])
        
    print(f"Total input edges: {len(edges_df)}")
    
    # 1. PiT Filtering: Drop edges that started strictly after the anchor date.
    edges_df = edges_df[edges_df['overlap_start'] <= t_anchor].copy()
    print(f"Edges remaining after PiT start filtering: {len(edges_df)}")
    
    # 2. Trim overlap_end to t_anchor (point-in-time closure of ongoing associations)
    effective_end = edges_df['overlap_end'].clip(upper=t_anchor)
    
    # 3. Compute overlap days
    O_days = (effective_end - edges_df['overlap_start']).dt.days
    edges_df['O_days'] = O_days
    
    # Only keep strictly positive overlaps
    edges_df = edges_df[edges_df['O_days'] > 0].copy()
    
    # Convert overlapping times effectively back into the row
    edges_df['t_h'] = effective_end
    
    # Compute Weights
    def compute_weight(row):
        h_norm = row['hub']
        h_type = row['hub_type']
        o_days = row['O_days']
        t_h = row['t_h']
        
        S_h = hub_sizes.get((h_norm, h_type), 50.0)

        b_h = b_company if h_type == 'company' else b_school
        if S_h < b_h:
            S_h = b_h
            
        log_size = math.log(S_h, b_h)
        if log_size <= 0:
            log_size = 1.0
            
        days_since_end = (t_anchor - t_h).days
        if days_since_end < 0:
            days_since_end = 0
            
        decay = math.exp(-lambda_decay * days_since_end)
        
        weight = (o_days / log_size) * decay
        return weight
        
    edges_df['weight'] = edges_df.apply(compute_weight, axis=1)
    
    # Phase 3 Modification: Do not group and sum weights.
    # Preserve the multiple overlapping records to allow chronological routing using 't_h'.
    final_df = edges_df[['u', 'v', 'hub', 'hub_type', 't_h', 'weight']].copy()
    
    out_path = f"data/weighted_graph_{t_anchor_str}.feather"
    final_df.to_feather(out_path)
    print(f"Saved {len(final_df)} multigraph weighted edges to {out_path}.")
    print("\n--- Top 10 Heaviest Distinct Edges ---")
    print(final_df.sort_values("weight", ascending=False).head(10))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--t-anchor", type=str, required=True, help="Anchor date YYYY-MM-DD")
    parser.add_argument("--b-company", type=float, default=3.0)
    parser.add_argument("--b-school", type=float, default=10.0)
    parser.add_argument("--lambda", dest="lmbda", type=float, default=0.001)
    args = parser.parse_args()
    
    query_graph(args.t_anchor, args.b_company, args.b_school, args.lmbda)
