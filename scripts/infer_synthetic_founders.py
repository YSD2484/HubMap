import os
import json
import argparse
import pandas as pd
import xgboost as xgb
from core.llm_clients import openai_client


def generate_synthetic_founders():
    print("Prompting GPT-4o-mini to hallucinate strictly formatted founder phenotypes...")
    
    prompt = """
    You are an expert Silicon Valley quantitative researcher. Invent 3 distinct startup founders:
    1. A Stanford dropout who is highly technically gifted but bootstrapped (has raised 0 prior dollars) and never held a senior role.
    2. A multi-time serial founder who previously built a unicorn (raised $50,000,000+) and held former VP titles at Google.
    3. A standard mid-tier developer from a state school who pivoted to a moderate startup (raised $1,500,000) and was a director once.
    
    Respond ONLY with a valid JSON Object containing a single key "founders" which maps to a list. Example:
    {"founders": [ {"name": "...", "persona": "...", "prior_amount_raised_usd": 0, "prior_senior_roles": 0, "most_recent_role": "...", "most_recent_degree": "..."} ]}
    """
    
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        response_format={"type": "json_object"}
    )
    
    content = json.loads(response.choices[0].message.content)
    return content['founders']


def infer_founders(t_anchor_str, model_path=None):
    feature_path = f"data/feature_matrix_{t_anchor_str}.feather"
    
    if model_path is None:
        model_path = f"data/xgb_model_{t_anchor_str}.json"
    
    if not os.path.exists(feature_path):
        raise FileNotFoundError(f"Feature matrix not found: {feature_path}")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"XGBoost model not found: {model_path}")
        
    print(f"Loading Historical Feature Matrix {t_anchor_str} for structural approximation...")
    df_base = pd.read_feather(feature_path)
    df_base['cap_bin'] = pd.qcut(df_base['prior_amount_raised_usd'].rank(method='first'), q=5, labels=False)
    
    clf = xgb.XGBClassifier()
    clf.load_model(model_path)
    model_features = clf.feature_names_in_
    
    founders = generate_synthetic_founders()
    
    results = []
    
    for f in founders:
        print(f"\nEvaluating Synthetic Profile: {f['name']} ({f['persona']})")
        print(f" -> Prior Capital: ${f['prior_amount_raised_usd']:,} | Prior Senior Roles: {f['prior_senior_roles']}")
        
        target_cap = float(f['prior_amount_raised_usd'])
        
        # Approximate bin based on capital level
        if target_cap == 0:
            similar_peers = df_base[df_base['cap_bin'] == 0]
        elif target_cap > 10000000:
            similar_peers = df_base[df_base['cap_bin'] == 4]
        else:
            similar_peers = df_base[df_base['cap_bin'] == 2]
            
        print(f" -> Abstracting 64D Node2Vec network tensors from {len(similar_peers)} identical peer topologies...")
        
        # Construct the explicit feature row
        row = {}
        for col in model_features:
            if col == 'prior_amount_raised_usd':
                row[col] = target_cap
            elif col == 'prior_senior_roles':
                row[col] = float(f['prior_senior_roles'])
            else:
                row[col] = similar_peers[col].median()
                
        df_infer = pd.DataFrame([row])[model_features]
        
        prob = clf.predict_proba(df_infer)[0, 1]
        percentile_score = prob * 100
        
        print("============================================================")
        print(f">>> Outlier Probability Score: {prob:.4f}")
        print(f">>> Likelihood of Terminal 5Y Success: {percentile_score:.2f}%")
        print("============================================================\n")
        
        f['outlier_probability'] = prob
        results.append(f)
        
    print("Generative Validation Loop Completed Successfully!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--t-anchor", type=str, default="2024-01-01", help="Anchor date YYYY-MM-DD")
    parser.add_argument("--model-path", type=str, default=None, help="Path to XGBoost model JSON")
    args = parser.parse_args()
    infer_founders(args.t_anchor, args.model_path)
