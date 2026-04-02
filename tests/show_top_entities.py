from core.db import get_session
from sqlalchemy import text

session = get_session()
res = session.execute(text("""
    SELECT c.name, COUNT(DISTINCT j.founder_id) as f_count
    FROM "Companies" c
    JOIN "Jobs" j ON c.id = j.company_id
    GROUP BY c.id, c.name
    ORDER BY f_count DESC
    LIMIT 20
"""))
print("Top 20 Companies:")
for r in res:
    print(f"{r[0]}: {r[1]}")

res2 = session.execute(text("""
    SELECT s.name, COUNT(DISTINCT e.founder_id) as f_count
    FROM "Schools" s
    JOIN "Educations" e ON s.id = e.school_id
    GROUP BY s.id, s.name
    ORDER BY f_count DESC
    LIMIT 20
"""))
print("\nTop 20 Schools:")
for r in res2:
    print(f"{r[0]}: {r[1]}")
