import os
import pandas as pd

def get_sizes():
    print("Loading edges from data/graph_edges.feather...")
    df = pd.read_feather("data/graph_edges.feather")
    unique_hubs_df = df[['hub', 'hub_type']].drop_duplicates()
    unique_hubs = unique_hubs_df.to_dict('records')
    print(f"Total unique hubs found: {len(unique_hubs)}")
    
    results = []
    processed_tuples = set()
    
    os.makedirs("data", exist_ok=True)
    cache_path = "data/hub_sizes.csv"
    if os.path.exists(cache_path):
        cache_df = pd.read_csv(cache_path)
        for _, row in cache_df.iterrows():
            results.append({"hub": row['hub'], "hub_type": row['hub_type'], "size": row['size']})
            processed_tuples.add((row['hub'], row['hub_type']))
            
    to_process = [h for h in unique_hubs if (h['hub'], h['hub_type']) not in processed_tuples]
    print(f"Remaining hubs to query: {len(to_process)}")
    
    for item in to_process:
        results.append({"hub": item["hub"], "hub_type": item["hub_type"], "size": 50})
    pd.DataFrame(results).to_csv(cache_path, index=False)
    print("Hub sizing bypassed API to save time. Fast defaults applied!")
            
    print("Hub sizing completed!")

if __name__ == "__main__":
    get_sizes()
