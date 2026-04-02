"""
scripts/train_model.py
----------------------
Trains a single-anchor XGBoost ranker with Optuna hyperparameter optimization.

This script trains an ``XGBRanker`` model using the ``rank:pairwise`` objective,
which learns to sort founders by their predicted future success *relative to one another*
rather than optimizing a global binary classification threshold.

Key design decisions:
    - **Target**: The binary label ``y`` is created by calling ``label_outlier()``
      globally (top 15% of ``future_outcome`` across all founders at the anchor).
    - **Future Outcome**: Computed by ``extract_future_outcome()`` via the strict
      PiT Valuation Waterfall evaluated at ``t_anchor + 5 years``.
    - **Loss**: ``rank:pairwise`` is optimized with NDCG as the evaluation metric.
    - **Hyperparameter Search**: Optuna runs 15 trials of Random Forest-style k-fold
      cross-validation, using ``StratifiedKFold`` with ``n_splits=3``.

Usage::
    python scripts/train_model.py --t-anchor YYYY-MM-DD
"""

import argparse
import os
import pandas as pd
import numpy as np
import optuna

import xgboost as xgb
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import ndcg_score
from utils.ml_utils import extract_future_outcome, label_outlier
import warnings

# Suppress pandas FutureWarnings and Optuna info
warnings.simplefilter(action='ignore', category=FutureWarning)
optuna.logging.set_verbosity(optuna.logging.WARNING)


def objective(trial, X, y):
    """Optuna objective: train an XGBRanker and return the mean cross-validated NDCG.

    Called by the Optuna study to evaluate a specific hyperparameter configuration.
    Uses 3-fold StratifiedKFold so that the positive-class ratio is balanced across
    splits. Each fold trains on the training split, predicts on the validation split,
    and computes NDCG (treating the whole fold as one query group).

    Args:
        trial (optuna.Trial): The current Optuna trial object.
        X (pd.DataFrame): Feature matrix.
        y (pd.Series): Binary target labels (0/1).

    Returns:
        float: Mean NDCG score across all cross-validation folds.
    """
    params = {
        'objective': 'rank:pairwise',
        'eval_metric': 'ndcg',
        'max_depth': trial.suggest_int('max_depth', 3, 9),
        'learning_rate': trial.suggest_float('learning_rate', 1e-3, 0.3, log=True),
        'subsample': trial.suggest_float('subsample', 0.5, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.5, 1.0),
        'gamma': trial.suggest_float('gamma', 0, 5),
        'min_child_weight': trial.suggest_int('min_child_weight', 1, 10),
        'n_estimators': 100,
        'random_state': 42,
        'enable_categorical': True
    }
    
    skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
    scores = []
    
    for train_idx, val_idx in skf.split(X, y):
        X_tr, X_va = X.iloc[train_idx], X.iloc[val_idx]
        y_tr, y_va = y.iloc[train_idx], y.iloc[val_idx]
        
        clf = xgb.XGBRanker(**params)
        clf.fit(X_tr, y_tr, group=[len(X_tr)], eval_set=[(X_va, y_va)], eval_group=[[len(X_va)]], verbose=False)
        preds = clf.predict(X_va)
        
        # Optimize on NDCG. ndcg_score expects 2D arrays shape (n_queries, n_items)
        score = ndcg_score([y_va.values], [preds])
        scores.append(score)
        
    return np.mean(scores)

def build_and_train(t_anchor_str):
    """Train an XGBRanker on the feature matrix for a given anchor date.

    Loads the pre-assembled feature matrix, computes the Valuation Waterfall
    target for ``t_anchor + 5 years``, labels the global top-15% as y=1,
    then runs Optuna to find the best XGBRanker hyperparameters. Trains the
    final model on the full dataset using the best found parameters.

    Args:
        t_anchor_str (str): Anchor date in ``YYYY-MM-DD`` format.
    """
    t_anchor = pd.to_datetime(t_anchor_str).normalize()
    feature_path = f"data/feature_matrix_{t_anchor_str}.feather"
    
    if not os.path.exists(feature_path):
        print(f"Feature matrix {feature_path} not found!")
        return
        
    print(f"Loading feature matrix from {feature_path}...")
    df = pd.read_feather(feature_path)
    print(f"Loaded {df.shape[0]} founders with {df.shape[1]} features.")
    
    # 1. Extract Outcome (using updated future outcome logic evaluating at anchor + 5 years)
    outcome_df = extract_future_outcome(t_anchor, df['id'].unique())
    df = df.merge(outcome_df, on='id', how='left')
    df['future_outcome'] = df['future_outcome'].fillna(0)
    
    # 2. Dynamic Relative Target (y) - Global Labeling
    print("Constructing Dynamic Global Targets (Top 15%)...")
    df['y'] = label_outlier(df)
    
    positive_rate = df['y'].mean()
    print(f"Created Target 'y'. Positive Class Ratio: {positive_rate:.2%} ({df['y'].sum()} / {len(df)})")
    
    # Assemble X
    drop_cols = ['id', 'future_outcome', 'most_recent_role', 'most_recent_degree', 'y']
    features = [c for c in df.columns if c not in drop_cols]
    
    X = df[features].copy()
    y = df['y']
    
    categorical_cols = ['primary_mafia_id', 'louvain_community_id']
    for col in categorical_cols:
        if col in X.columns:
            X[col] = X[col].astype('category')
    
    if df['y'].sum() < 2:
        print("Not enough positive examples to train effectively.")
        return
    
    # 4. Optuna
    print("Initiating XGBoost Hyperparameter Optimization (Optuna)...")
    study = optuna.create_study(direction='maximize')
    study.optimize(lambda trial: objective(trial, X, y), n_trials=15)
    
    print("\n=== Best Model Configuration ===")
    print(f"Optimal NDCG: {study.best_value:.4f}")
    print("Hyperparameters:", study.best_params)
    
    # Train Final
    best_params = study.best_params
    best_params['objective'] = 'rank:pairwise'
    best_params['n_estimators'] = 100
    best_params['random_state'] = 42
    best_params['enable_categorical'] = True
    
    clf = xgb.XGBRanker(**best_params)
    clf.fit(X, y, group=[len(X)])
    
    # Feature Importances
    importances = clf.feature_importances_
    idx = np.argsort(importances)[::-1][:10]
    
    print("\nTop 10 Feature Importances:")
    for i in idx:
        print(f"{features[i]}: {importances[i]:.4f}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--t-anchor", type=str, required=True, help="Anchor date YYYY-MM-DD")
    args = parser.parse_args()
    build_and_train(args.t_anchor)
