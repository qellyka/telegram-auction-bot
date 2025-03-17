from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from config import DB_URL
from app.db.models import Base

engine = create_async_engine(
        url=DB_URL,
        echo=True,
        pool_size=5,
        max_overflow=10,
    )

async_session = async_sessionmaker(engine)

async def setup_db() -> None:
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
