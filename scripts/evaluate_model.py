"""
scripts/evaluate_model.py
--------------------------
Walk-forward Out-of-Sample (OOS) evaluation for founder ranking models.

This script implements the strict temporal evaluation framework:

    1. Loads pre-assembled feature matrices for both a training and a test anchor.
    2. Enforces a minimum 5-year embargo between anchors to prevent target-window overlap.
    3. Extracts future outcomes for both anchors using the Valuation Waterfall at
       ``t_anchor + 5 years``.
    4. Trains an XGBoost classifier on the training data.
    5. Predicts on the unseen test cohort.
    6. Reports multiple alpha-generation metrics: Global PR-AUC, Cohort-Stratified
       Precision@K (k=10, 20), and Intra-Cohort Spearman's Rho.

Note:
    This script retains cohort binning for *evaluation grouping only* (Precision@K
    and Spearman breakdown per cohort). It does **not** influence label generation,
    which is handled globally by ``label_outlier()``.

Usage::
    python scripts/evaluate_model.py --train-anchor YYYY-MM-DD --test-anchor YYYY-MM-DD
"""

import argparse
import os
import pandas as pd
import numpy as np
from dateutil.relativedelta import relativedelta

import xgboost as xgb
from sklearn.metrics import average_precision_score
from scipy.stats import spearmanr

from utils.ml_utils import extract_future_outcome, label_outlier

import warnings
warnings.simplefilter(action='ignore')


def evaluate(train_anchor_strs, test_anchor_str):
    """Run walk-forward evaluation comparing a training anchor to an embargoed test anchor.

    Performs the full evaluation pipeline:
        1. Validates the 5-year time embargo between anchors.
        2. Loads feature matrices for both anchors.
        3. Computes cohort bins on the training set and projects frozen boundaries
           onto the test set to prevent look-ahead bias in stratified reporting.
        4. Extracts ``future_outcome`` using the Valuation Waterfall for both anchors.
        5. Labels both sets globally (top 15% = y=1) via ``label_outlier``.
        6. Trains an XGBoost classifier (classifier used here for probability scores
           to feed into PR-AUC and Spearman diagnostics).
        7. Reports PR-AUC, Cohort Precision@K, and Spearman's Rho.

    Raises:
        AssertionError: If the gap between ``test_anchor`` and ``train_anchor`` is
            less than 5 years, indicating a risk of target-window data leakage.

    Args:
        train_anchor_strs (list of str): List of historical training cutoff dates.
        test_anchor_str (str): Out-of-sample validation date in ``YYYY-MM-DD``.
            Must be at least 5 years after the LATEST train anchor.
    """
    train_anchors = [pd.to_datetime(s).normalize() for s in train_anchor_strs]
    test_anchor = pd.to_datetime(test_anchor_str).normalize()
    
    # Embargo Check (against latest train anchor)
    latest_train = max(train_anchors)
    diff_years = relativedelta(test_anchor, latest_train).years
    if diff_years < 5:
        raise AssertionError(f"TEMPORAL LEAKAGE DETECTED! Test anchor {test_anchor_str} is only {diff_years} years ahead of Latest Train anchor {latest_train.date()}. A strict 5-year embargo is required.")
        
    print(f"Embargo Verified: Training Window closes at {latest_train.date() + pd.DateOffset(years=5)} | Testing Anchor begins {test_anchor.date()}")
    
    train_dfs = []
    for s in train_anchor_strs:
        p = f"data/feature_matrix_{s}.feather"
        if os.path.exists(p):
            tdf = pd.read_feather(p)
            out_t = extract_future_outcome(pd.to_datetime(s).normalize(), tdf['id'].unique())
            tdf = tdf.merge(out_t, on='id', how='left')
            tdf['future_outcome'] = tdf['future_outcome'].fillna(0)
            tdf['pct_rank'] = tdf['future_outcome'].rank(pct=True, method='max')
            tdf['y'] = label_outlier(tdf)
            train_dfs.append(tdf)
            
    df_train = pd.concat(train_dfs, ignore_index=True)
    
    test_path = f"data/feature_matrix_{test_anchor_str}.feather"
    if not os.path.exists(test_path):
        print(f"Missing test feature matrix: {test_path}")
        return
    df_test = pd.read_feather(test_path)
    
    print(f"Pooled Train Shape: {df_train.shape}, Test Shape: {df_test.shape}")
    
    # 1. Baseline State Extraction & Train Cohort Binning
    print("Computing 5x5 Quantile Boundaries on TRAINING Set exclusively...")
    
    # Extract explicit training bin boundaries
    train_net_series, net_bins = pd.qcut(df_train['pagerank'].rank(method='first'), q=5, retbins=True, labels=False)
    train_cap_series, cap_bins = pd.qcut(df_train['prior_amount_raised_usd'].rank(method='first'), q=5, retbins=True, labels=False)
    
    df_train['net_bin'] = train_net_series
    df_train['cap_bin'] = train_cap_series
    df_train['cohort_id'] = df_train['net_bin'].astype(str) + "_" + df_train['cap_bin'].astype(str)
    
    # Extend outer bin limits to infinity to capture extreme out-of-sample data dynamically
    net_bins[0], net_bins[-1] = -np.inf, np.inf
    cap_bins[0], cap_bins[-1] = -np.inf, np.inf
    
    print("Projecting frozen threshold boundaries blindly onto TEST Set (Preventing Look-Ahead Bias)...")
    # Extracted training cohort limits
    _, raw_net_bins = pd.qcut(df_train['pagerank'], q=5, retbins=True, duplicates='drop')
    _, raw_cap_bins = pd.qcut(df_train['prior_amount_raised_usd'], q=5, retbins=True, duplicates='drop')
    raw_net_bins[0], raw_net_bins[-1] = -np.inf, np.inf
    raw_cap_bins[0], raw_cap_bins[-1] = -np.inf, np.inf
    
    # Overwrite the original training cohorts with the strict raw boundaries logic (to synchronize perfectly mapped semantics)
    df_train['net_bin'] = pd.cut(df_train['pagerank'], bins=raw_net_bins, labels=False, include_lowest=True)
    df_train['cap_bin'] = pd.cut(df_train['prior_amount_raised_usd'], bins=raw_cap_bins, labels=False, include_lowest=True)
    df_train['cohort_id'] = df_train['net_bin'].astype(str) + "_" + df_train['cap_bin'].astype(str)

    df_test['net_bin'] = pd.cut(df_test['pagerank'], bins=raw_net_bins, labels=False, include_lowest=True)
    df_test['cap_bin'] = pd.cut(df_test['prior_amount_raised_usd'], bins=raw_cap_bins, labels=False, include_lowest=True)
    df_test['cohort_id'] = df_test['net_bin'].astype(str) + "_" + df_test['cap_bin'].astype(str)
    
    out_test = extract_future_outcome(test_anchor, df_test['id'].unique())
    df_test = df_test.merge(out_test, on='id', how='left')
    df_test['future_outcome'] = df_test['future_outcome'].fillna(0)
    df_test['pct_rank'] = df_test['future_outcome'].rank(pct=True, method='max')
    df_test['y'] = label_outlier(df_test)
    
    print(f"Train Targets Y=1: {df_train['y'].sum()} / {len(df_train)}")
    print(f"Test Targets Y=1: {df_test['y'].sum()} / {len(df_test)}")
    
    # 3. XGBoost Modeling
    drop_cols = ['id', 'net_bin', 'cap_bin', 'cohort_id', 'future_outcome', 'pct_rank', 'most_recent_role', 'most_recent_degree', 'y']
    features = [c for c in df_train.columns if c not in drop_cols]
    
    X_train = df_train[features].copy()
    y_train = df_train['y']
    
    X_test = df_test[features].copy()
    
    categorical_cols = ['primary_mafia_id', 'louvain_community_id']
    for col in categorical_cols:
        if col in X_train.columns:
            X_train[col] = X_train[col].astype('category')
            X_test[col] = X_test[col].astype('category')
            
    print(f"X_train dtypes checked. Categorical columns: {X_train[categorical_cols].dtypes}")
    
    print("Training Optimally Bounded Model on Historical Trajectory...")
    # Best params extracted via Optuna theoretically
    best_params = {
        'objective': 'binary:logistic',
        'eval_metric': 'aucpr',
        'scale_pos_weight': 19,
        'max_depth': 3,
        'learning_rate': 0.02,
        'subsample': 0.95,
        'colsample_bytree': 0.6,
        'gamma': 3.9,
        'n_estimators': 150,
        'random_state': 42,
        'enable_categorical': True
    }
    
    clf = xgb.XGBClassifier(**best_params)
    clf.fit(X_train, y_train, verbose=False)
    
    print("Predicting Walk-Forward Test Data...")
    df_test['pred_prob'] = clf.predict_proba(X_test)[:, 1]
    
    # 4. Evaluation Engine (Alpha Generation Metrics)
    print("\n" + "="*50)
    print("Walk-Forward Phase 6 Alpha Diagnostics")
    print("="*50)
    
    global_pr = average_precision_score(df_test['y'], df_test['pred_prob'])
    random_base = df_test['y'].mean()
    print(f"[1] Global PR-AUC: {global_pr:.4f} (Baseline Random Chance: {random_base:.4f})")
    
    print("\n[2] Cohort-Stratified Precision at K (Testing Deep Contextual Edge)")
    
    k_targets = [10, 20]
    for k_val in k_targets:
        print(f"\nEvaluating Top {k_val} Outliers Per Distinct Starting Cohort:")
        total_hits = 0
        total_attempts = 0
        for cohort_id, sub_df in df_test.groupby('cohort_id'):
            if len(sub_df) < k_val:
                continue
                
            y_actual = sub_df['y'].values
            if y_actual.sum() == 0:
                continue # Impossible to hit 1 since there were absolutely no outliers generated
                
            sorted_pred = sub_df.sort_values('pred_prob', ascending=False).head(k_val)
            hits = sorted_pred['y'].sum()
            
            total_hits += hits
            total_attempts += k_val
            print(f" - Cohort {cohort_id} (n={len(sub_df)}): Detected {hits}/{k_val} Outliers")
            
        if total_attempts > 0:
            print(f"Overall Cohort Hit Rate at K={k_val}: {total_hits/total_attempts:.2%}")
            
    print("\n[3] Predicted Prob vs Actual Outcome Continuous Rank-Order Correlation")
    
    rhos = []
    pvals = []
    
    for cohort_id, sub_df in df_test.groupby('cohort_id'):
        if len(sub_df) > 5 and sub_df['pred_prob'].nunique() > 1:
            # Spearman correlation comparing exactly predicted prob to the continuous outcome percentile
            r, p = spearmanr(sub_df['pred_prob'], sub_df['pct_rank'])
            if not np.isnan(r):
                rhos.append(r)
                pvals.append(p)
                
    if rhos:
        avg_rho = np.mean(rhos)
        print(f"Average Intra-Cohort Spearman's Rho: {avg_rho:.4f}")
        print("This verifies if the model's confidence directly correlates to the Founder's final absolute standing irrespective of the binary cutoffs.\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-anchors", type=str, nargs="+", required=True, help="Historical training cutoff dates")
    parser.add_argument("--test-anchor", type=str, required=True, help="Out of sample strictly embargoed validation YYYY-MM-DD")
    args = parser.parse_args()
    evaluate(args.train_anchors, args.test_anchor)
