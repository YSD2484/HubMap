
from core.db import get_session, Founder, Job, Education, Company, School
from sqlalchemy.sql.expression import func

def main():
    session = get_session()
    
    # Get 5 random founders
    founders = session.query(Founder).order_by(func.random()).limit(5).all()
    
    print("=== 5 Random Founders Overview ===\n")
    
    for founder in founders:
        print(f"Founder: {founder.name} (ID: {founder.id})")
        
        jobs = session.query(Job, Company.name).join(Company, Job.company_id == Company.id).filter(Job.founder_id == founder.id).order_by(Job.start_year.desc()).all()
        print("  Jobs:")
        if not jobs:
            print("    None on record.")
        for j, c_name in jobs:
            start = j.start_year if j.start_year else "Unknown"
            end = j.end_year if j.end_year and j.end_year != 2026 else "Present"
            print(f"    - {j.role} @ {c_name} ({start} - {end})")
            
        educations = session.query(Education, School.name).join(School, Education.school_id == School.id).filter(Education.founder_id == founder.id).order_by(Education.start_year.desc()).all()
        print("  Education:")
        if not educations:
            print("    None on record.")
        for e, s_name in educations:
            start = e.start_year if e.start_year else "Unknown"
            end = e.end_year if e.end_year else "Unknown"
            degree = e.degree if e.degree else "Unknown Degree"
            print(f"    - {degree} from {s_name} ({start} - {end})")
        
        print("-" * 50)
        
    session.close()

if __name__ == "__main__":
    main()
