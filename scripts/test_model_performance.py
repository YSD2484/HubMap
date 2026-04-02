import argparse
import os
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import precision_recall_curve, average_precision_score, confusion_matrix, classification_report, roc_auc_score, brier_score_loss
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.calibration import calibration_curve
import shap

from utils.ml_utils import extract_future_outcome, label_outlier

def run_performance_tests(t_anchor_str, out_dir):
    t_anchor = pd.to_datetime(t_anchor_str).normalize()
    feature_path = f"data/feature_matrix_{t_anchor_str}.feather"
    
    print(f"Loading data from {feature_path}...")
    df = pd.read_feather(feature_path)
    
    # Cohort Binning
    print("Binning Baseline Starting States (3x3 grid)...")
    df['net_bin'] = pd.qcut(df['pagerank'].rank(method='first'), q=3, labels=False)
    df['cap_bin'] = pd.qcut(df['prior_amount_raised_usd'].rank(method='first'), q=3, labels=False)
    df['cohort_id'] = df['net_bin'].astype(str) + "_" + df['cap_bin'].astype(str)
    
    # Target Extraction
    outcome_df = pd.read_feather(f"data/y_target_{t_anchor_str}.feather")
    df = df.merge(outcome_df, on='id', how='left')
    df['future_outcome'] = df['future_outcome'].fillna(0)
    
    # Target Formulation
    print("Constructing Sub-Cohort Targets (Top 15% relative variance)...")
    df['y'] = df.groupby('cohort_id', group_keys=False).apply(label_outlier)
    
    # Filter valid rows (only keep if target exists)
    drop_cols = ['id', 'net_bin', 'cap_bin', 'cohort_id', 'future_outcome', 'most_recent_role', 'most_recent_degree', 'y']
    features = [c for c in df.columns if c not in drop_cols]
    
    X = df[features].copy()
    y = df['y']
    
    categorical_cols = ['primary_mafia_id', 'louvain_community_id']
    for col in categorical_cols:
        if col in X.columns:
            X[col] = X[col].astype('category')
    
    if y.sum() < 2:
        print("Not enough positive examples to run cross-validation!")
        return
        
    print(f"Dataset securely loaded. Shape: {X.shape}. Class Balance: {y.mean():.2%} positive.")
    
    # Stratified OOF Predictions
    print("Running Stratified 5-Fold Cross Validation for Out-of-Fold (OOF) Metrics...")
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    oof_preds = np.zeros(len(y))
    oof_preds_binary = np.zeros(len(y))
    
    feature_importances = np.zeros(len(features))
    
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
    
    for fold, (train_idx, val_idx) in enumerate(skf.split(X, y)):
        X_tr, X_va = X.iloc[train_idx], X.iloc[val_idx]
        y_tr = y.iloc[train_idx]
        
        clf = xgb.XGBClassifier(**best_params)
        clf.fit(X_tr, y_tr, verbose=False)
        
        preds = clf.predict_proba(X_va)[:, 1]
        oof_preds[val_idx] = preds
        
        feature_importances += clf.feature_importances_ / skf.n_splits
    
    # 1. Classification Metrics
    global_pr = average_precision_score(y, oof_preds)
    global_roc = roc_auc_score(y, oof_preds)
    brier = brier_score_loss(y, oof_preds)
    random_base = y.mean()
    
    print("\n--- Model Success Diagnostics ---")
    print(f"Global OOF PR-AUC: {global_pr:.4f} (Baseline guessing would yield {random_base:.4f})")
    print(f"Global OOF ROC-AUC: {global_roc:.4f}")
    print(f"Brier Score Loss: {brier:.4f}")
    print(f"Lift Over Random: {global_pr / random_base:.2f}x multiplier")
    
    # Find optimal threshold via F1
    precision, recall, thresholds = precision_recall_curve(y, oof_preds)
    fscore = (2 * precision * recall) / (precision + recall + 1e-9)
    ix = np.argmax(fscore)
    optimal_threshold = thresholds[ix] if ix < len(thresholds) else 0.5
    
    print(f"\nOptimal Operating Threshold (Max F1): {optimal_threshold:.4f}")
    oof_preds_binary = (oof_preds >= optimal_threshold).astype(int)
    
    print("\nClassification Report (At Optimal Threshold):")
    print(classification_report(y, oof_preds_binary))
    
    os.makedirs(out_dir, exist_ok=True)
    sns.set_theme(style="whitegrid")
    
    # 2. Plot Precision-Recall Curve (The absolute source of truth for imbalanced data)
    plt.figure(figsize=(10, 6))
    plt.plot(recall, precision, marker='.', label=f'XGBoost (PR-AUC={global_pr:.3f})')
    plt.axhline(y=random_base, color='r', linestyle='--', label=f'Random Chance ({random_base:.3f})')
    plt.scatter(recall[ix], precision[ix], marker='o', color='black', label='Optimal F1 Threshold', zorder=5)
    plt.xlabel('Recall (True Positive Rate)')
    plt.ylabel('Precision (Positive Predictive Value)')
    plt.title(f'Continuous Outlier Detection Precision-Recall Curve ({t_anchor.year} Cohort)')
    plt.legend()
    plt.savefig(os.path.join(out_dir, f'pr_curve_{t_anchor_str}.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    # 3. Decile Lift Chart (Cumulative Gains equivalents)
    df_lift = pd.DataFrame({'y_true': y, 'y_prob': oof_preds})
    df_lift = df_lift.sort_values('y_prob', ascending=False)
    df_lift['decile'] = pd.qcut(np.arange(len(df_lift)), 10, labels=False)
    
    lift_rates = df_lift.groupby('decile')['y_true'].mean()
    plt.figure(figsize=(10, 6))
    sns.barplot(x=lift_rates.index + 1, y=lift_rates.values, palette='Blues_d')
    plt.axhline(y=random_base, color='r', linestyle='--', label='Random Baseline')
    plt.xlabel('Prediction Probability Decile (1 = Highest Confidence)')
    plt.ylabel('Outlier Hit Rate (%)')
    plt.title('Decile Lift Chart (Model Sorting Power)')
    plt.legend()
    plt.savefig(os.path.join(out_dir, f'decile_lift_{t_anchor_str}.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    # 4. Confusion Matrix
    cm = confusion_matrix(y, oof_preds_binary)
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=False)
    plt.xlabel('Predicted Label')
    plt.ylabel('True Label')
    plt.title(f'Confusion Matrix (Threshold: {optimal_threshold:.2f})')
    plt.savefig(os.path.join(out_dir, f'confusion_matrix_{t_anchor_str}.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    # 5. Feature Importances
    fi_df = pd.DataFrame({
        'Feature': features,
        'Importance': feature_importances
    }).sort_values('Importance', ascending=False).head(15)
    
    plt.figure(figsize=(10, 8))
    sns.barplot(x='Importance', y='Feature', data=fi_df, palette='viridis')
    plt.title('Top 15 Predictive Structural Features (OOF Average)')
    plt.savefig(os.path.join(out_dir, f'feature_importance_{t_anchor_str}.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    # 6. Calibration Curve
    prob_true, prob_pred = calibration_curve(y, oof_preds, n_bins=10)
    plt.figure(figsize=(8, 8))
    plt.plot(prob_pred, prob_true, marker='o', label='XGBoost')
    plt.plot([0, 1], [0, 1], linestyle='--', color='k', label='Perfectly Calibrated')
    plt.xlabel('Mean Predicted Probability')
    plt.ylabel('Fraction of Positives')
    plt.title(f'Calibration Curve (Reliability Diagram) - {t_anchor_str}')
    plt.legend()
    plt.savefig(os.path.join(out_dir, f'calibration_curve_{t_anchor_str}.png'), dpi=300, bbox_inches='tight')
    plt.close()

    clf_final = xgb.XGBClassifier(**best_params)
    clf_final.fit(X, y)
    
    # 7. SHAP Summary Plot
    explainer = shap.TreeExplainer(clf_final)
    shap_values = explainer.shap_values(X)
    plt.figure()
    shap.summary_plot(shap_values, X, show=False)
    plt.savefig(os.path.join(out_dir, f'shap_summary_{t_anchor_str}.png'), dpi=300, bbox_inches='tight')
    plt.close()

    clf_final.save_model(os.path.join(out_dir, f'xgb_model_{t_anchor_str}.json'))
    print(f"\nFinal Global XGBoost Configuration successfully serialized to {out_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--t-anchor", type=str, required=True)
    parser.add_argument("--out-dir", type=str, required=True)
    args = parser.parse_args()
    
    run_performance_tests(args.t_anchor, args.out_dir)
