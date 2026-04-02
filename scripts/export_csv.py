import csv
import os
from core.db import get_session, Founder, Company, School, Job, Education, Hub

def export_model_to_csv(model_class, session, output_dir: str = "."):
    """
    Exports the contents of an ORM model's table to a CSV file.
    """
    records = session.query(model_class).all()
    if not records:
        print(f"No records found for {model_class.__tablename__}.")
        return

    # Extract column names from the SQLAlchemy model
    columns = [column.name for column in model_class.__mapper__.columns]
    
    filepath = os.path.join(output_dir, f"{model_class.__tablename__}.csv")
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        
        for record in records:
            writer.writerow([getattr(record, col) for col in columns])
            
    print(f"Exported {model_class.__tablename__} -> {filepath}")

def export_all_tables(output_dir: str = "."):
    """
    Exports all core models to CSV.
    """
    session = get_session()
    models = [Founder, Company, School, Job, Education, Hub]
    
    print(f"Starting export of {len(models)} tables...")
    for model in models:
        export_model_to_csv(model, session, output_dir)
        
    print("All tables exported successfully.")
    session.close()

if __name__ == "__main__":
    export_all_tables()
