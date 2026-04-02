from core.db import Base, get_engine

engine = get_engine()
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
print("Reinitialized DB.")
