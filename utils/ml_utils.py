"""
utils/ml_utils.py
-----------------
Machine learning utility functions for the Vela Founder Prediction Pipeline.

This module handles all target construction logic used during model training.
It enforces strict Point-in-Time (PiT) semantics so that no future information
can contaminate feature generation or label assignment.

Key functions:
    - calculate_founder_success: Computes a founder's peak enterprise value using
      a strict Valuation Waterfall evaluated at a given t_anchor.
    - extract_future_outcome: Evaluates the Valuation Waterfall at t_anchor + 5
      years to generate the training target for each founder.
    - label_outlier: Assigns binary y=1 to the global top 15% of future outcomes,
      across all founders at a given anchor (no cohort binning).
"""

import pandas as pd
from core.config import settings
from utils.utils import normalize_date
from founder_data import load_founder_profiles

def dict_get(obj, key, default=None):
    """Safely retrieve an attribute from either a dict or an object instance.
    
    This helper exists because founder profile objects from the `founder_data` package
    can surface as either Pydantic models (attribute access) or plain dicts (key access),
    depending on the parsing path. This normalizes both access patterns.

    Args:
        obj: A dict or any object.
        key (str): The attribute or key to look up.
        default: Value to return if the key/attribute is absent. Defaults to None.

    Returns:
        The value at the given key/attribute, or `default` if not found.
    """
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)

def calculate_founder_success(profile, t_anchor) -> dict:
    """Calculate a founder's Peak Enterprise Value at a strict Point-in-Time anchor.

    This function implements the canonical Valuation Waterfall used to define
    absolute outlier success. It enforces temporal correctness by ignoring any
    company founded after `t_anchor` and dropping any sub-events (funding rounds,
    IPOs, acquisitions) whose dates exceed `t_anchor`.

    Valuation Tiers (evaluated in strict descending priority):
        Tier 1 — Public Exit: Max ``valuation_usd`` from valid IPOs.
        Tier 2 — M&A Exit:   Max ``price_usd`` from valid acquisitions.
        Tier 3 — Private:    Max ``post_money_valuation_usd`` from valid funding rounds.
        Tier 4 — Imputed:    5× the max ``amount_raised_usd`` from valid rounds
                             (assumes 20% dilution per round).
        Fallback:            0.0 if all tiers are null or empty.

    Null-safety: Any date field that is None or unparseable is treated as invalid
    and causes that event to be silently dropped, preventing data leakage.

    Args:
        profile: A founder profile object (Pydantic model or dict) containing
            a ``crunchbase.founded_organizations`` structure.
        t_anchor (datetime | str): The Point-in-Time cutoff. All events strictly
            after this date are excluded.

    Returns:
        dict: A dictionary with the following keys:
            - ``success_score_usd`` (float): The founder's peak enterprise value.
            - ``is_imputed`` (bool): True if the winning value came from Tier 4.
            - ``winning_company_name`` (str | None): Name of the company that
              generated the peak score.
            - ``valid_companies_count`` (int): Number of companies the founder
              had started on or before `t_anchor`.
    """
    t_anchor = pd.to_datetime(t_anchor)
    cb = dict_get(profile, "crunchbase", {}) if profile else {}
    orgs = dict_get(cb, "founded_organizations", []) or []
    
    overall_max_val = 0.0
    overall_is_imputed = False
    overall_winning_company = None
    valid_companies_count = 0
    
    for org in orgs:
        f_on = dict_get(org, "founded_on") or dict_get(org, "started_on")
        f_on = normalize_date(f_on)
        
        # Step 1: Drop companies founded after t_anchor or with invalid dates.
        if not f_on or f_on > t_anchor:
            continue
            
        valid_companies_count += 1
        
        comp_val = 0.0
        comp_is_imputed = False
        
        # Tier 1: Public Exit (IPO valuation)
        ipos = dict_get(org, "ipos", []) or []
        valid_ipos = [i for i in ipos if normalize_date(dict_get(i, "went_public_on")) and normalize_date(dict_get(i, "went_public_on")) <= t_anchor and dict_get(i, "valuation_usd") is not None]
        
        if valid_ipos:
            comp_val = max([float(dict_get(i, "valuation_usd")) for i in valid_ipos])
            comp_is_imputed = False
        else:
            # Tier 2: M&A Exit (acquisition price)
            acqs = dict_get(org, "acquisitions", []) or []
            valid_acqs = [a for a in acqs if normalize_date(dict_get(a, "acquired_on")) and normalize_date(dict_get(a, "acquired_on")) <= t_anchor and dict_get(a, "price_usd") is not None]
            
            if valid_acqs:
                comp_val = max([float(dict_get(a, "price_usd")) for a in valid_acqs])
                comp_is_imputed = False
            else:
                rounds = dict_get(org, "funding_rounds", []) or []
                valid_rounds = [r for r in rounds if normalize_date(dict_get(r, "announced_on")) and normalize_date(dict_get(r, "announced_on")) <= t_anchor]
                
                # Tier 3: Post-money valuation from funding rounds
                tier3_rounds = [r for r in valid_rounds if dict_get(r, "post_money_valuation_usd") is not None]
                if tier3_rounds:
                    comp_val = max([float(dict_get(r, "post_money_valuation_usd")) for r in tier3_rounds])
                    comp_is_imputed = False
                else:
                    # Tier 4: Imputed valuation = 5× max amount raised (20% dilution assumption)
                    tier4_rounds = [r for r in valid_rounds if dict_get(r, "amount_raised_usd") is not None]
                    if tier4_rounds:
                        max_raised = max([float(dict_get(r, "amount_raised_usd")) for r in tier4_rounds])
                        comp_val = max_raised * 5.0
                        comp_is_imputed = True
        
        # Step 3: Keep whichever company gives the highest valuation
        if comp_val > overall_max_val:
            overall_max_val = comp_val
            overall_is_imputed = comp_is_imputed
            overall_winning_company = dict_get(org, "name") or "Unknown"

    return {
        "success_score_usd": float(overall_max_val),
        "is_imputed": overall_is_imputed,
        "winning_company_name": overall_winning_company,
        "valid_companies_count": valid_companies_count
    }

def extract_future_outcome(t_anchor, founder_ids):
    """Extract the 5-year future success score for each founder using the Valuation Waterfall.

    For each founder in `founder_ids`, the function evaluates the Valuation Waterfall
    (``calculate_founder_success``) at exactly ``t_anchor + 5 years``. This produces
    a continuous score representing the founder's peak enterprise value as of that
    future date, forming the raw training signal.

    The 5-year forward window is chosen to give enough time for a company to exit
    (IPO / acquisition) or close a meaningful private round, while keeping the
    look-ahead horizon constant across all temporal cross-sections.

    Note:
        This function intentionally uses the same strict PiT logic as
        ``calculate_founder_success``, but the anchor passed in is ``t_anchor + 5 years``.
        No information is leaked from beyond that target horizon.

    Args:
        t_anchor (pd.Timestamp): The training anchor date. The target is evaluated at
            ``t_anchor + 5 years``.
        founder_ids (iterable): Iterable of founder DB UUID strings to evaluate.

    Returns:
        pd.DataFrame: A DataFrame with two columns:
            - ``id`` (str): Founder UUID.
            - ``future_outcome`` (float): Peak enterprise value at ``t_anchor + 5 years``.
    """
    print(f"Extracting 5-year future financial outcomes for anchor {t_anchor.date()}...")
    t_end = t_anchor + pd.DateOffset(years=5)
    
    profiles = load_founder_profiles(n=settings.MAX_PROFILES, refresh_cache=False)
    
    from utils.utils import get_founder_name_to_id_map
    name_to_id = get_founder_name_to_id_map()
    
    outcomes = []
    founder_set = set(founder_ids)
    
    for p in profiles:
        f_id = name_to_id.get(p.name)
        if not f_id or f_id not in founder_set:
            continue
            
        success_info = calculate_founder_success(p, t_end)
        
        outcomes.append({
            'id': f_id, 
            'future_outcome': success_info['success_score_usd']
        })
        
    import gc
    gc.collect()
    return pd.DataFrame(outcomes)

def label_outlier(df_or_series):
    """Assign binary labels marking the global top 15% of founders as outlier successes.

    Labels y=1 are assigned to founders whose ``future_outcome`` score falls at or above
    the 85th percentile **globally** across the full dataset, not within cohort bins.
    Only founders with a positive (non-zero) future outcome can receive y=1, preventing
    a degenerate label assignment when the dataset skews heavily toward zero.

    This global approach replaced earlier cohort-relative labeling so the model learns
    to rank founders by absolute enterprise value rather than relative starting position.

    Args:
        df_or_series (pd.DataFrame | pd.Series): Either a full DataFrame with a
            ``future_outcome`` column, or a raw numeric Series.

    Returns:
        pd.Series: Binary integer Series (0/1) aligned to the input index.
    """
    if isinstance(df_or_series, pd.DataFrame):
        target = pd.Series(0, index=df_or_series.index)
        series = df_or_series['future_outcome']
    else:
        target = pd.Series(0, index=df_or_series.index)
        series = df_or_series
        
    if len(series) > 0:
        threshold = series.quantile(0.85)
        mask = (series >= threshold) & (series > 0)
        target[mask] = 1
    return target
