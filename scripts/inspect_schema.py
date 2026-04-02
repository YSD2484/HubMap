import sys
import os
import pandas as pd
from founder_data import load_founder_profiles

profiles = list(load_founder_profiles(n=10, refresh_cache=False))

for p in profiles:
    orgs = getattr(getattr(p, "crunchbase", None), "founded_organizations", []) or []
    for org in orgs:
        print("Org:", getattr(org, "name", "Unknown"))
        if hasattr(org, "funding_rounds"):
            print("  funding_rounds type:", type(org.funding_rounds))
            if org.funding_rounds:
                print("  first round:", dir(org.funding_rounds[0]))
        if hasattr(org, "ipos"):
            print("  ipos type:", type(org.ipos))
            if org.ipos:
                print("  first ipo:", dir(org.ipos[0]))
        if hasattr(org, "acquisitions"):
            print("  acquisitions type:", type(org.acquisitions))
            if org.acquisitions:
                print("  first acq:", dir(org.acquisitions[0]))
        break
    if orgs:
        break
