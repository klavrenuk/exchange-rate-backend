from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.deps import get_session
from app.services.iea import downloader, sender
from app.common.models import Chart, SentChart
import os

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


@router.get("/charts")
async def list_charts(session: AsyncSession = Depends(get_session)):
    res = await session.execute(select(Chart).order_by(Chart.discovered_at.desc()))
    charts = res.scalars().all()
    out = []
    for c in charts:
        res2 = await session.execute(select(SentChart).where(SentChart.chart_id == c.id))
        sent = res2.scalar_one_or_none() is not None
        images = []
        folder = c.local_path or os.path.join("./data/charts", c.slug)
        if os.path.exists(folder):
            for fname in sorted(os.listdir(folder)):
                if fname.lower().endswith(('.png', '.jpg', '.jpeg', '.svg', '.webp', '.gif')):
                    images.append(f"/files/charts/{c.slug}/{fname}")
        out.append({
            "id": c.id,
            "url": c.url,
            "slug": c.slug,
            "title": c.title,
            "discovered_at": c.discovered_at.isoformat() if c.discovered_at else None,
            "downloaded_at": c.downloaded_at.isoformat() if c.downloaded_at else None,
            "has_files": c.has_files,
            "local_path": c.local_path,
            "sent": sent,
            "images": images,
        })
    return out
