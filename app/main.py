from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.logging import setup_logging
from app.db.init_db import init_db
from app.api.v1.router import api_router
from app.tasks import scheduler

logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await scheduler.start_scheduler()
    logger.info("Application started")
    yield
    await scheduler.shutdown_scheduler()
    logger.info("Application stopped")


app = FastAPI(title="Exchange Rate Backend", version="1.0.0", lifespan=lifespan)
app.include_router(api_router)
