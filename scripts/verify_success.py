import pandas as pd
from utils.ml_utils import calculate_founder_success, extract_future_outcome, label_outlier
import scripts.train_pooled_model
import scripts.train_model
from core.db import get_session
from founder_data import load_founder_profiles

print("Imports successful!")

# Test on a single founder
profiles = list(load_founder_profiles(n=10, refresh_cache=False))
if profiles:
    p = profiles[0]
    t_anchor = pd.to_datetime('2020-01-01')
    res = calculate_founder_success(p, t_anchor)
    print("Calculate Founder Success Result:", res)

print("All tests passed.")
