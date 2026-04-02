from core.db import get_session, Company, School, Hub
from sqlalchemy import func

def verify():
    session = get_session()

    # Verify Companies & Schools uniqueness
    companies_count = session.query(Company).count()
    distinct_companies = session.query(func.count(func.distinct(Company.normalized_name))).scalar()
    
    schools_count = session.query(School).count()
    distinct_schools = session.query(func.count(func.distinct(School.normalized_name))).scalar()
    
    print(f"Total Companies: {companies_count}, Distinct Normalized Names: {distinct_companies}")
    assert companies_count == distinct_companies, "Duplicate companies detected!"
    
    print(f"Total Schools: {schools_count}, Distinct Normalized Names: {distinct_schools}")
    assert schools_count == distinct_schools, "Duplicate schools detected!"

    print("SUCCESS: 1 ID per Company and 1 ID per School constraint verified.")

    # Show some hub statistics
    hubs_count = session.query(Hub).count()
    print(f"Total Hub Records: {hubs_count}")

    if hubs_count > 0:
        sample_hub = session.query(Hub).limit(1).all()[0]
        print(f"Sample Hub: Type={sample_hub.hub_type}, Members={len(sample_hub.founder_ids)}")
        
    session.close()

if __name__ == "__main__":
    verify()
