import os
from sqlalchemy import Column, String, DateTime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime

# Database config
DB_HOST = os.getenv("DB_HOST", "db")
DB_NAME = os.getenv("DB_NAME", "claims_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres_pass")

# PostgreSQL connection string format
SQLALCHEMY_DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

# Engine, Base, and Session setup for SQLAlchemy
engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True)
Base = declarative_base()
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Claims table schema
class Claim(Base):
    """
    Defines the structure for the 'claims' table in PostgreSQL.
    """
    __tablename__ = "claims"

    claim_id = Column(String, primary_key=True, index=True, nullable=False)
    decision = Column(String, nullable=False)
    reason = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now())

# Create database table
def create_db_and_tables():
    with engine.begin() as conn:
        Base.metadata.create_all(conn)

# Dependency to get database session
async def get_db():
    async with SessionLocal() as session:
        yield session
