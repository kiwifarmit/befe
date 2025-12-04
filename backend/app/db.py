import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.models import (
    Base,  # Import UserCredits to ensure it's registered with Base.metadata
)

# UserCredits is imported in models.py and registered via Base.metadata

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(DATABASE_URL, echo=True, future=True)


async def init_db():
    """
    Initialize database tables.
    Creates all tables defined in models (User, UserCredits, etc.).

    Note: For fresh database creation (after docker compose down -v),
    this will create the new structure without the credits column in user table.
    For existing databases, run the SQL migration script first.
    """
    async with engine.begin() as conn:
        # Uncomment the line below to drop all tables and recreate (WARNING: destroys all data)
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
