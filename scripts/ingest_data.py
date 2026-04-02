"""
scripts/ingest_data.py
-----------------------
Populates the PostgreSQL database with normalized founder, company, school, job,
education, and hub records from the raw ``founder_data`` BigQuery profiles.

This is the first script to run in the ML pipeline. It reads up to ``MAX_PROFILES``
founder profiles (via the ``founder_data`` package) and, for each one:
    1. Collects them in-memory first to avoid slow N+1 ORM queries.
    2. Uses bulk chunked SQL statements (on_conflict_do_nothing) for lightning-fast speeds.
    3. At the end, aggregates the ``Hubs`` table (which company/school each founder
       belongs to) using a raw SQL upsert for performance.

Usage::
    python scripts/ingest_data.py
"""

from founder_data import load_founder_profiles
from core.db import (
    get_session, init_db,
    Founder, Company, School, Job, Education
)
from utils.utils import normalize_string
from utils.profile_helpers import extract_jobs, extract_educations, extract_company_name, extract_school_name

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import text
import uuid

def generate_hubs(session):
    print("Generating Hubs table via Upsert...")
    # Update Company Hubs
    company_hub_sql = """
    INSERT INTO "Hubs" (hub_type, hub_id, founder_ids)
    SELECT 'company', company_id, array_agg(DISTINCT founder_id)
    FROM "Jobs"
    GROUP BY company_id
    ON CONFLICT (hub_type, hub_id) 
    DO UPDATE SET 
        founder_ids = ARRAY(
            SELECT DISTINCT unnest("Hubs".founder_ids || EXCLUDED.founder_ids)
        );
    """
    session.execute(text(company_hub_sql))
    
    # Update School Hubs
    school_hub_sql = """
    INSERT INTO "Hubs" (hub_type, hub_id, founder_ids)
    SELECT 'school', school_id, array_agg(DISTINCT founder_id)
    FROM "Educations"
    GROUP BY school_id
    ON CONFLICT (hub_type, hub_id) 
    DO UPDATE SET 
        founder_ids = ARRAY(
            SELECT DISTINCT unnest("Hubs".founder_ids || EXCLUDED.founder_ids)
        );
    """
    session.execute(text(school_hub_sql))
    session.commit()
    print("Hubs Generation Complete.")

def process_profiles(limit: int = 15):
    """
    Parse a number of profiles and populate the postgres DB modularly using fast bulk inserts.
    """
    session = get_session()
    
    profiles_gen = load_founder_profiles(n=limit, refresh_cache=False)
    
    company_cache = {}
    school_cache = {}
    founder_cache = set()
    
    founders_to_insert = []
    companies_to_insert = []
    schools_to_insert = []
    jobs_to_insert = []
    educations_to_insert = []
    
    # Pre-fetch existing ones just in case script is run without DB reset
    for c in session.query(Company.id, Company.normalized_name).all():
        company_cache[c.normalized_name] = c.id
    for s in session.query(School.id, School.normalized_name).all():
        school_cache[s.normalized_name] = s.id
    for f in session.query(Founder.name).all():
        founder_cache.add(f.name.lower())
    
    for idx, profile in enumerate(profiles_gen):
        if idx % 1000 == 0:
            print(f"[{idx}/{limit}] Parsing profiles in memory...")
            
        fname_lower = profile.name.lower()
        if fname_lower in founder_cache:
            continue
            
        fid = uuid.uuid4()
        founder_cache.add(fname_lower)
        founders_to_insert.append({"id": fid, "name": profile.name})
        
        for job in extract_jobs(profile):
            company_name = extract_company_name(job)
            if not company_name: continue
            norm_name = normalize_string(company_name)
            if not norm_name: continue
            
            if norm_name not in company_cache:
                cid = uuid.uuid4()
                company_cache[norm_name] = cid
                companies_to_insert.append({"id": cid, "name": company_name, "normalized_name": norm_name})
            else:
                cid = company_cache[norm_name]
                
            start_y = getattr(job, "started_on", None)
            end_y = getattr(job, "ended_on", None)
            
            jobs_to_insert.append({
                "founder_id": fid,
                "company_id": cid,
                "role": getattr(job, "title", ""),
                "start_year": start_y.year if start_y else None,
                "end_year": end_y.year if end_y else None
            })
            
        for edu in extract_educations(profile):
            sz_name = extract_school_name(edu)
            if not sz_name: continue
            norm_name = normalize_string(sz_name)
            if not norm_name: continue
            
            if norm_name not in school_cache:
                sid = uuid.uuid4()
                school_cache[norm_name] = sid
                schools_to_insert.append({"id": sid, "name": sz_name, "normalized_name": norm_name})
            else:
                sid = school_cache[norm_name]
                
            start_y = getattr(edu, "started_on", None)
            ended_on = getattr(edu, "completed_on", None) or getattr(edu, "ended_on", None)
            
            educations_to_insert.append({
                "founder_id": fid,
                "school_id": sid,
                "degree": getattr(edu, "degree", ""),
                "start_year": start_y.year if start_y else None,
                "end_year": ended_on.year if ended_on else None
            })
            
    print(f"\nCollected {len(founders_to_insert)} new founders. Bulk inserting into DB...")
    
    def chunked_insert(table, data, unique_cols, chunk_size=5000):
        for i in range(0, len(data), chunk_size):
            session.execute(insert(table).values(data[i:i+chunk_size]).on_conflict_do_nothing(index_elements=unique_cols))
            session.commit()
            
    if founders_to_insert:
        chunked_insert(Founder, founders_to_insert, ['id'])
    if companies_to_insert:
        chunked_insert(Company, companies_to_insert, ['normalized_name'])
    if schools_to_insert:
        chunked_insert(School, schools_to_insert, ['normalized_name'])
    if jobs_to_insert:
        chunked_insert(Job, jobs_to_insert, ['founder_id', 'company_id', 'role', 'start_year'])
    if educations_to_insert:
        chunked_insert(Education, educations_to_insert, ['founder_id', 'school_id', 'degree', 'start_year'])
        
    print("Finished base record insertion.")
    generate_hubs(session)
    session.close()

if __name__ == "__main__":
    init_db()
    process_profiles(20000)

