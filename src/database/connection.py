"""
Database connection and configuration
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from pathlib import Path

# Database URL - defaults to SQLite for development
# Construct proper path to database file
ROOT_DIR = Path(__file__).parents[2]  # Go up 2 levels from src/database to project root
DB_PATH = ROOT_DIR / 'data' / 'db' / 'legal_ai.db'
# Create the database directory if it doesn't exist
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
# Create database URL with proper path format
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite+aiosqlite:///{DB_PATH}")

# Create async engine
engine = create_async_engine(
    DATABASE_URL, 
    echo=True,
    future=True,
)

# Create session factory
async_session = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Base class for declarative models
Base = declarative_base()

async def create_db_and_tables():
    """Create database and tables on startup"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_session():
    """Dependency for getting database sessions"""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
