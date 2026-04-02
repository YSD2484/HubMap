"""
scripts/build_graph.py
----------------------
Builds the raw unipartite founder co-association graph.

For each founder, this script extracts their job tenures, education periods,
and founded-organization tenures. It then computes pairwise overlaps between
any two founders who shared the same normalized hub (company or school). Each
overlap produces an undirected edge in the multigraph with metadata including:
    - the hub identifier (normalized name)
    - the hub type ('company' or 'school')
    - the overlap start and end dates

The resulting edge list is saved to ``data/graph_edges.feather`` and later
processed by ``query_graph.py`` which applies PiT filtering and edge weighting.

Usage::
    python scripts/build_graph.py
"""

import itertools
from collections import defaultdict
import pandas as pd
from core import settings
from utils.utils import normalize_string, normalize_date
from utils.profile_helpers import extract_jobs, extract_educations, extract_company_name, extract_school_name, extract_founded_orgs
from founder_data import load_founder_profiles
def parse_tenures(profile, founder_id, hub_tenures):
    """Extract all dated tenures (jobs, educations, founded orgs) for one founder.

    For each professional or educational association, a tenure record is appended
    to the shared ``hub_tenures`` dictionary under the appropriate normalized hub key.
    Only tenures with a valid start date that is in the past (before today) and that
    are logically ordered (start < end) are retained.

    Open-ended tenures (no end date) are closed at today's date.

    Args:
        profile: A founder profile object from ``load_founder_profiles``.
        founder_id (str): DB UUID string for this founder.
        hub_tenures (defaultdict): Shared accumulator mapping (hub_norm, hub_type)
            to a list of tenure records with keys ``founder_id``, ``start``, ``end``.
    """
    today = pd.to_datetime('today').normalize()
    
    # 1. Jobs
    for j in extract_jobs(profile):
        c_name = extract_company_name(j)
        if not c_name:
            continue
        hub_norm = normalize_string(c_name)
        if not hub_norm:
            continue
        
        start = normalize_date(getattr(j, "started_on", None))
        end = normalize_date(getattr(j, "ended_on", None), fallback=today)
        
        if start and start < end and start <= today:
            hub_tenures[(hub_norm, "company")].append({"founder_id": str(founder_id), "start": start, "end": end})

    # 2. Educations
    for e in extract_educations(profile):
        s_name = extract_school_name(e)
        if not s_name:
            continue
        hub_norm = normalize_string(s_name)
        if not hub_norm:
            continue
        
        start = normalize_date(getattr(e, "started_on", None))
        end = normalize_date(getattr(e, "completed_on", None) or getattr(e, "ended_on", None), fallback=today)
        
        if start and start < end and start <= today:
            hub_tenures[(hub_norm, "school")].append({"founder_id": str(founder_id), "start": start, "end": end})
            
    # 3. Founded Orgs
    for org in extract_founded_orgs(profile):
        c_name = getattr(org, "name", None) or getattr(org, "organization_name", None)
        if not c_name:
            continue
        hub_norm = normalize_string(c_name)
        if not hub_norm:
            continue
        
        start = normalize_date(getattr(org, "started_on", None) or getattr(org, "founded_on", None))
        end = normalize_date(getattr(org, "ended_on", None), fallback=today)
        
        if start and start < end and start <= today:
            hub_tenures[(hub_norm, "company")].append({"founder_id": str(founder_id), "start": start, "end": end})

def build_graph():
    """Construct and persist the raw unipartite founder-to-founder edge list.

    Iterates over all loaded founder profiles, calls ``parse_tenures`` for each
    to populate a shared hub-tenure map, then exhaustively computes pairwise
    temporal overlaps across founders sharing the same hub. Only edges with a
    strictly positive overlap duration are included.

    Multi-edges from the same pair of founders at the same hub are deduplicated
    by keeping the earliest overlap start date.

    Output is written to ``data/graph_edges.feather``.
    """
    from utils.utils import get_founder_name_to_id_map  # deferred to avoid circular import with DB session
    
    print("Loading founders from DB to map names to UUIDs...")
    name_to_id = get_founder_name_to_id_map()
    
    print(f"Mapped {len(name_to_id)} founders from DB.")
    
    hub_tenures = defaultdict(list)
    print("Loading profiles (using cache or fetching from BigQuery)...")
    profiles = load_founder_profiles(n=settings.MAX_PROFILES, refresh_cache=False)
    
    count = 0
    for p in profiles:
        f_id = name_to_id.get(p.name)
        if not f_id:
            continue
        parse_tenures(p, f_id, hub_tenures)
        count += 1
        if count % 500 == 0:
            print(f"Parsed {count} profiles...")
            
    print("Projecting to Unipartite Graph (Founder <-> Founder)...")
    edge_map = {}
    
    for (hub_norm, hub_type), tenures in hub_tenures.items():
        if len(tenures) < 2:
            continue
            
        for t1, t2 in itertools.combinations(tenures, 2):
            f1, f2 = t1["founder_id"], t2["founder_id"]
            if f1 == f2:
                continue
                
            u, v = (f1, f2) if f1 < f2 else (f2, f1)
            
            overlap_start = max(t1["start"], t2["start"])
            overlap_end = min(t1["end"], t2["end"])
            
            if overlap_start <= overlap_end:
                key = (u, v, hub_norm, hub_type)
                # Keep earliest overlap start per tuple
                if key not in edge_map or overlap_start < edge_map[key][0]:
                    edge_map[key] = (overlap_start, overlap_end)
                
    print(f"Total unique overlapping edges found: {len(edge_map)}")
    
    if edge_map:
        # Convert map to lists for fast DataFrame construction
        u_list, v_list, hub_list, type_list, start_list, end_list = [], [], [], [], [], []
        for (u, v, hub, hub_type), (overlap_start, overlap_end) in edge_map.items():
            u_list.append(u)
            v_list.append(v)
            hub_list.append(hub)
            type_list.append(hub_type)
            start_list.append(overlap_start)
            end_list.append(overlap_end)
            
        df = pd.DataFrame({
            'u': u_list,
            'v': v_list,
            'hub': hub_list,
            'hub_type': type_list,
            'overlap_start': start_list,
            'overlap_end': end_list
        })
        
        import os
        os.makedirs("data", exist_ok=True)
        out_path = "data/graph_edges.feather"
        df.to_feather(out_path)
        print(f"Saved {len(df)} unique unipartite edges to {out_path}.")
    else:
        print("No edges found. Graph is empty.")

if __name__ == "__main__":
    build_graph()
