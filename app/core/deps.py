from typing import AsyncGenerator
from app.core.base import AsyncSessionLocal


async def get_session() -> AsyncGenerator:
    async with AsyncSessionLocal() as session:
        yield session
