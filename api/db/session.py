"""Async database session for FastAPI."""
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://llair:llair_dev@localhost:5432/little_lairs",
)

engine = create_async_engine(DATABASE_URL, pool_size=5, max_overflow=10)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    async with async_session() as session:
        yield session
