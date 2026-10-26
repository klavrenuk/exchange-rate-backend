from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app.core.logging import setup_logging
from app.core.init_db import init_db
from app.api.v1.router import api_router
from app.tasks import scheduler
import os

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("./data/charts", exist_ok=True)
os.makedirs("./data/reports", exist_ok=True)
app.mount("/files", StaticFiles(directory="./data"), name="files")

app.include_router(api_router)
