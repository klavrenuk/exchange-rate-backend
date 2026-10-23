from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.deps import get_session
from app.services.iea import downloader, sender

router = APIRouter()


@router.post("/discover")
async def discover(session: AsyncSession = Depends(get_session)):
    await downloader.discover_charts(session)
    return {"status": "ok"}


@router.post("/download-new")
async def download_new(session: AsyncSession = Depends(get_session)):
    await downloader.download_new_charts(session)
    return {"status": "ok"}


@router.post("/send-new")
async def send_new(session: AsyncSession = Depends(get_session)):
    await sender.send_new_charts(session)
    return {"status": "ok"}
