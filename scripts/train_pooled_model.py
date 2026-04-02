"""
scripts/train_pooled_model.py
------------------------------
Trains a cross-sectional "Super Model" XGBRanker pooled over multiple anchor years.

This script is the primary training entry point for production-ready models. Instead
of training on a single anchor's data, it stacks feature matrices from multiple
historical anchor dates into one master dataset, increasing sample diversity and
reducing the risk of overfitting to any single market epoch.

Key design decisions:
    - **Target**: ``label_outlier()`` is applied globally *within each anchor year*
      (top 15% of ``future_outcome`` at that anchor), then all labels are pooled.
    - **Future Outcome**: Computed by the PiT Valuation Waterfall at
      ``t_anchor + 5 years`` for each anchor independently.
    - **Loss**: ``rank:pairwise``, grouped by ``anchor_year`` so the model learns to
      rank founders correctly within each historical cross-section.
    - **No Cohort Binning**: Rankings are applied globally within each anchor, replacing
      the previous 2D cohort-relative approach.

The trained ranker is saved to ``data/xgb_pooled_model.json``.

Usage::
    python scripts/train_pooled_model.py --train-anchors YYYY-MM-DD [YYYY-MM-DD ...]
"""

import argparse
import os
import pandas as pd
import numpy as np
import xgboost as xgb
from utils.ml_utils import extract_future_outcome, label_outlier
import warnings

warnings.simplefilter(action='ignore', category=FutureWarning)

def train_pooled(train_anchors):
    """Train and save the pooled XGBRanker (Super Model) across multiple anchor dates.

    For each anchor in ``train_anchors``:
        1. Loads the pre-assembled feature matrix.
        2. Calls ``extract_future_outcome`` to get Valuation Waterfall targets.
        3. Applies ``label_outlier`` globally (top 15%).
        4. Tags rows with ``anchor_year`` for group-based ranking.

    All anchors are concatenated into one master DataFrame which is then sorted by
    ``anchor_year`` and used to derive the ``group`` array for XGBoost's LTR interface.
    Feature importances (top 15) are printed after training.

    Args:
        train_anchors (list[str]): List of anchor date strings in ``YYYY-MM-DD`` format.
            Each must have a corresponding ``data/feature_matrix_{anchor}.feather`` file.
    """
    dfs = []
    
    for t_str in train_anchors:
        t_anchor = pd.to_datetime(t_str).normalize()
        feature_path = f"data/feature_matrix_{t_str}.feather"
        
        if not os.path.exists(feature_path):
            print(f"Skipping {t_str}: Feature matrix not found.")
            continue
            
        print(f"Loading {t_str} features...")
        df = pd.read_feather(feature_path)
        
        # 1. Outcomes
        outcome_df = pd.read_feather(f"data/y_target_{t_str}.feather")
        df = df.merge(outcome_df, on='id', how='left')
        df['future_outcome'] = df['future_outcome'].fillna(0)
        
        # 2. Labeling (y) - Global within anchor
        df['y'] = label_outlier(df)
        
        # Add anchor identifier for tracking and grouping
        df['anchor_year'] = t_anchor.year
        
        dfs.append(df)
        
    if not dfs:
        print("No training data found!")
        return
        
    master_df = pd.concat(dfs, ignore_index=True)
    
    # Sort by group id (anchor_year) required for ranking
    master_df = master_df.sort_values('anchor_year').reset_index(drop=True)
    
    print(f"Master pooled dataset shape: {master_df.shape}")
    print(f"Total positive examples (y=1): {master_df['y'].sum()}")
    
    # Group sizes for XGBoost ranking
    groups = master_df.groupby('anchor_year').size().values
    
    # Assemble X
    drop_cols = ['id', 'future_outcome', 'most_recent_role', 'most_recent_degree', 'y', 'anchor_year']
    features = [c for c in master_df.columns if c not in drop_cols]
    
    X = master_df[features].copy()
    y = master_df['y']
    
    categorical_cols = ['primary_mafia_id', 'louvain_community_id']
    for col in categorical_cols:
        if col in X.columns:
            X[col] = X[col].astype('category')
    
    # Train Super Model with robust parameters for ranking
    best_params = {
        'objective': 'rank:pairwise',
        'eval_metric': 'ndcg',
        'max_depth': 5,
        'learning_rate': 0.02,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'n_estimators': 300,
        'random_state': 42,
        'enable_categorical': True
    }
    
    if y.nunique() < 2:
        print("Error: Targeted y has only one class. Cannot train XGBoost on a single class.")
        return

    print("Training Pooled Super Model...")
    # NOTE: rank:pairwise does not use scale_pos_weight
    clf = xgb.XGBRanker(**best_params)
    clf.fit(X, y, group=groups)
    
    out_path = "data/xgb_pooled_model.json"
    clf.save_model(out_path)
    print(f"Pooled Super Model saved to {out_path}")
    
    # Feature Importances
    importances = clf.feature_importances_
    idx = np.argsort(importances)[::-1][:15]
    print("\nTop 15 Pooled Feature Importances:")
    for i in idx:
        print(f"{features[i]}: {importances[i]:.4f}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-anchors", nargs="+", required=True, help="List of anchors YYYY-MM-DD")
    args = parser.parse_args()
    train_pooled(args.train_anchors)
