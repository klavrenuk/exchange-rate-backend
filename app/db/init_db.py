import asyncio
from app.db.base import Base, engine
import app.db.models  # noqa


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


if __name__ == "__main__":
    asyncio.run(init_db())
    print("DB initialized")
