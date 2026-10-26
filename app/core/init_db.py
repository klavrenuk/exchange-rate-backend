import asyncio
from app.core.base import Base, engine
import app.common.models  # noqa


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn, checkfirst=True))


if __name__ == "__main__":
    asyncio.run(init_db())
    print("DB initialized")
