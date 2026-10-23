from typing import AsyncGenerator
from app.db.base import AsyncSessionLocal


async def get_session() -> AsyncGenerator:
    async with AsyncSessionLocal() as session:
        yield session
