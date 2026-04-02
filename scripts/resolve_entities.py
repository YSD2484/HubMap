from core.db import get_session, Company, School
from rapidfuzz import fuzz
from sqlalchemy import text
from core.llm_clients import openai_client
from collections import defaultdict

def ask_llm(api_key, ent1, ent2, entity_type="company"):
    prompt = f"Are the following two {entity_type} names referring to the exact same organization in the context of professional profiles? Reply with EXACTLY 'YES' or 'NO' and nothing else.\n1. {ent1}\n2. {ent2}"
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=5
        )
        ans = response.choices[0].message.content.strip().upper()
        return "YES" in ans
    except Exception as e:
        print(f"LLM Error: {e}")
        return False

def merge_entities(session, canonical_id, duplicate_id, entity_type):
    if entity_type == "company":
        # Merge Jobs
        session.execute(text("""
            UPDATE "Jobs" 
            SET company_id = :canonical_id 
            WHERE company_id = :duplicate_id 
              AND NOT EXISTS (
                  SELECT 1 FROM "Jobs" j2 
                  WHERE j2.founder_id = "Jobs".founder_id 
                    AND j2.company_id = :canonical_id 
                    AND COALESCE(j2.role, '') = COALESCE("Jobs".role, '') 
                    AND COALESCE(j2.start_year, 0) = COALESCE("Jobs".start_year, 0)
              )
        """), {"canonical_id": canonical_id, "duplicate_id": duplicate_id})
        
        session.execute(text("""DELETE FROM "Jobs" WHERE company_id = :duplicate_id"""), {"duplicate_id": duplicate_id})
        session.execute(text("""DELETE FROM "Companies" WHERE id = :duplicate_id"""), {"duplicate_id": duplicate_id})
        
    elif entity_type == "school":
        # Merge Educations
        session.execute(text("""
            UPDATE "Educations" 
            SET school_id = :canonical_id 
            WHERE school_id = :duplicate_id 
              AND NOT EXISTS (
                  SELECT 1 FROM "Educations" e2 
                  WHERE e2.founder_id = "Educations".founder_id 
                    AND e2.school_id = :canonical_id 
                    AND COALESCE(e2.degree, '') = COALESCE("Educations".degree, '') 
                    AND COALESCE(e2.start_year, 0) = COALESCE("Educations".start_year, 0)
              )
        """), {"canonical_id": canonical_id, "duplicate_id": duplicate_id})
        
        session.execute(text("""DELETE FROM "Educations" WHERE school_id = :duplicate_id"""), {"duplicate_id": duplicate_id})
        session.execute(text("""DELETE FROM "Schools" WHERE id = :duplicate_id"""), {"duplicate_id": duplicate_id})


def resolve_type(session, entity_class, entity_type):
    print(f"\n--- Resolving {entity_type}s ---")
    entities = session.query(entity_class.id, entity_class.name, entity_class.normalized_name).order_by(entity_class.normalized_name).all()
    
    # Track deleted ids so we don't process them
    deleted_ids = set()
    merges_done = 0
    
    print(f"Total {entity_type}s: {len(entities)}")
    
    groups = defaultdict(list)
    for c in entities:
        if len(c.normalized_name) >= 3:
            groups[c.normalized_name[:3]].append(c)
        else:
            groups[c.normalized_name].append(c)
            
    processed = 0
    for prefix, group_entities in groups.items():
        if len(group_entities) < 2:
            processed += len(group_entities)
            continue
            
        for i in range(len(group_entities)):
            processed += 1
            if processed % 5000 == 0:
                print(f"Processed {processed}/{len(entities)}...")
                
            c1 = group_entities[i]
            if c1.id in deleted_ids:
                continue
                
            for j in range(i + 1, len(group_entities)):
                c2 = group_entities[j]
                if c2.id in deleted_ids:
                    continue
                    
                if len(c1.normalized_name) < 5 or len(c2.normalized_name) < 5:
                    continue
                    
                should_merge = False
                reason = ""
                
                score = fuzz.ratio(c1.normalized_name, c2.normalized_name)
                if score >= 90:
                    should_merge = True
                    reason = "High Fuzzy Match"
                else:
                    if c1.normalized_name.startswith(c2.normalized_name) or c2.normalized_name.startswith(c1.normalized_name):
                        diff = abs(len(c1.normalized_name) - len(c2.normalized_name))
                        if 0 < diff < 10:
                            should_merge = True
                            reason = "Prefix Match"
                
                if should_merge:
                    # Decide canonical (shortest normalized name usually represents the base company)
                    if len(c1.normalized_name) <= len(c2.normalized_name):
                        canonical_id, duplicate_id = c1.id, c2.id
                        canon_name, dup_name = c1.name, c2.name
                    else:
                        canonical_id, duplicate_id = c2.id, c1.id
                        canon_name, dup_name = c2.name, c1.name
                    
                    print(f"[{reason}] Merging '{dup_name}' into '{canon_name}'")
                    
                    try:
                        merge_entities(session, canonical_id, duplicate_id, entity_type)
                        session.commit()
                        deleted_ids.add(duplicate_id)
                        merges_done += 1
                        
                        if c1.id == duplicate_id:
                            break
                    except Exception as e:
                        session.rollback()
                        print(f"Failed to merge {duplicate_id} into {canonical_id}: {e}")

    print(f"Completed! Merged {merges_done} {entity_type}s.")

def main():
    session = get_session()
    
    resolve_type(session, Company, "company")
    resolve_type(session, School, "school")
    
    print("\n--- Rebuilding Hubs ---")
    from scripts.ingest_data import generate_hubs
    generate_hubs(session)

if __name__ == "__main__":
    main()
