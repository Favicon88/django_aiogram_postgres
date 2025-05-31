from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from config import DB_URL

# from .env file:
# DB_URL=postgresql+asyncpg://login:password@localhost:5432/db_name

engine = create_async_engine(DB_URL, echo=False, hide_parameters=True)

session_maker = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)
