"""
core/db.py
----------
SQLAlchemy ORM models and database session utilities for the Vela platform.

Defines the relational schema used to store normalized founder graph data:
    - ``Founders``  : One row per unique founder (name + UUID primary key).
    - ``Companies`` : De-duplicated company entities with normalized names.
    - ``Schools``   : De-duplicated school entities with normalized names.
    - ``Jobs``      : Many-to-many link between Founders and Companies,
                     with optional role title and start/end years.
    - ``Educations``: Many-to-many link between Founders and Schools,
                     with optional degree and start/end years.
    - ``Hubs``      : Aggregated cluster records mapping a company/school UUID
                     to the array of founder UUIDs associated with it.
                     Used as the basis for co-association graph construction.

All tables use PostgreSQL-specific types (UUID, ARRAY). Connection parameters
are read from ``core.config.settings`` which sources them from the ``.env`` file.
"""

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid
from core import settings

Base = declarative_base()

class Founder(Base):
    __tablename__ = 'Founders'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    
    jobs = relationship("Job", back_populates="founder")
    educations = relationship("Education", back_populates="founder")

class Company(Base):
    __tablename__ = 'Companies'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    normalized_name = Column(String, unique=True, nullable=False)

    jobs = relationship("Job", back_populates="company")

class School(Base):
    __tablename__ = 'Schools'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    normalized_name = Column(String, unique=True, nullable=False)

    educations = relationship("Education", back_populates="school")

class Job(Base):
    __tablename__ = 'Jobs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    founder_id = Column(UUID(as_uuid=True), ForeignKey('Founders.id'), nullable=False, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey('Companies.id'), nullable=False, index=True)
    role = Column(String)
    start_year = Column(Integer)
    end_year = Column(Integer)

    __table_args__ = (
        UniqueConstraint('founder_id', 'company_id', 'role', 'start_year', name='uq_job'),
    )

    founder = relationship("Founder", back_populates="jobs")
    company = relationship("Company", back_populates="jobs")

class Education(Base):
    __tablename__ = 'Educations'
    id = Column(Integer, primary_key=True, autoincrement=True)
    founder_id = Column(UUID(as_uuid=True), ForeignKey('Founders.id'), nullable=False, index=True)
    school_id = Column(UUID(as_uuid=True), ForeignKey('Schools.id'), nullable=False, index=True)
    degree = Column(String)
    start_year = Column(Integer)
    end_year = Column(Integer)

    __table_args__ = (
        UniqueConstraint('founder_id', 'school_id', 'degree', 'start_year', name='uq_education'),
    )

    founder = relationship("Founder", back_populates="educations")
    school = relationship("School", back_populates="educations")

class Hub(Base):
    __tablename__ = 'Hubs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    hub_type = Column(String, nullable=False) # 'company' or 'school'
    hub_id = Column(UUID(as_uuid=True), nullable=False)
    founder_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=False)

    __table_args__ = (
        UniqueConstraint('hub_type', 'hub_id', name='uq_hub'),
    )

def get_engine():
    """Create and return a SQLAlchemy engine using settings from ``core.config``.

    Constructs the DSN from the ``POSTGRES_*`` environment variables and
    creates a new connection pool. Called at the start of any DB operation.

    Returns:
        sqlalchemy.engine.Engine: A connected engine instance.
    """
    user = settings.POSTGRES_USER
    password = settings.POSTGRES_PASSWORD
    host = settings.POSTGRES_HOST
    port = settings.POSTGRES_PORT
    db = settings.POSTGRES_DB
    
    dsn = f"postgresql://{user}:{password}@{host}:{port}/{db}"
    engine = create_engine(dsn)
    return engine

def init_db():
    """Create all ORM-mapped tables in the database if they do not already exist.

    Safe to call multiple times (idempotent). Does not drop or modify existing
    tables. Should be run once during initial project setup.
    """
    engine = get_engine()
    Base.metadata.create_all(engine)
    print("Database tables initialized successfully.")

def get_session():
    """Create and return a new SQLAlchemy session.

    Each call creates a fresh session bound to a new engine connection pool.
    Callers are responsible for closing the session (``session.close()``) after use.

    Returns:
        sqlalchemy.orm.Session: A new database session.
    """
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()

if __name__ == "__main__":
    init_db()
