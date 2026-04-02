import os
import glob
import pandas as pd
from utils.ml_utils import extract_future_outcome, label_outlier

def analyze_mafia_success(min_count=5):
    dfs = []
    
    # Locate all feature matrices
    feature_files = glob.glob("data/feature_matrix_*.feather")
    if not feature_files:
        print("No feature matrices found in data/")
        return
        
    for f in feature_files:
        t_str = f.split("_")[-1].replace(".feather", "")
        t_anchor = pd.to_datetime(t_str)
        
        print(f"Processing anchor {t_str}...")
        df = pd.read_feather(f)
        
        # Get outcomes
        outcome_df = extract_future_outcome(t_anchor, df['id'].unique())
        df = df.merge(outcome_df, on='id', how='left')
        df['future_outcome'] = df['future_outcome'].fillna(0)
        
        # Label successes (top 15%)
        df['y'] = label_outlier(df)
        
        # Only keep necessary columns to save memory
        dfs.append(df[['id', 'primary_mafia_id', 'y']])
        
    if not dfs:
        return
        
    master_df = pd.concat(dfs, ignore_index=True)
    
    global_success_rate = master_df['y'].mean()
    print(f"\nTotal founders processed across all anchors: {len(master_df)}")
    print(f"Global Base Success Rate: {global_success_rate:.2%}\n")
    
    # Filter out founders without a mafia
    mafia_df = master_df[master_df['primary_mafia_id'] != 'none'].copy()
    
    # Group by mafia
    stats = mafia_df.groupby('primary_mafia_id').agg(
        founder_count=('id', 'count'),
        successes=('y', 'sum')
    ).reset_index()
    
    stats['success_rate'] = stats['successes'] / stats['founder_count']
    stats['multiplier'] = stats['success_rate'] / global_success_rate
    
    # Filter for minimum count and sort by multiplier
    valid_stats = stats[stats['founder_count'] >= min_count]
    top_mafias = valid_stats.sort_values('multiplier', ascending=False)
    
    print(f"=== Top Mafias by Success Likelihood Multiplier (Min {min_count} founders) ===")
    print(f"{'Company & Period':<35} | {'Count':<5} | {'Successes':<9} | {'Success Rate':<12} | {'Multiplier':<10}")
    print("-" * 80)
    
    for _, row in top_mafias.head(20).iterrows():
        comp_period = row['primary_mafia_id']
        count = int(row['founder_count'])
        succ = int(row['successes'])
        ratehat = row['success_rate']
        mult = row['multiplier']
        
        print(f"{comp_period:<35} | {count:<5} | {succ:<9} | {ratehat:>7.2%}      | {mult:>8.2f}x")

if __name__ == "__main__":
    analyze_mafia_success(min_count=5)
