import pandas as pd
import sys
import os
from utils.ml_utils import extract_future_outcome

def main():
    anchor = sys.argv[1]
    out_path = f"data/y_target_{anchor}.feather"
    if os.path.exists(out_path):
        print(f"Target already cached for {anchor}")
        return
        
    feat_path = f"data/feature_matrix_{anchor}.feather"
    df = pd.read_feather(feat_path)
    y_target = extract_future_outcome(pd.to_datetime(anchor), df['id'].values)
    y_target.to_feather(out_path)
    print(f"Saved {out_path}")

if __name__ == "__main__":
    main()
