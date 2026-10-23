from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.deps import get_session
from app.db.models import Currency, Rate, Chart, SentChart, JobRun

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/status/overview")
async def overview(session: AsyncSession = Depends(get_session)):
    currencies = await session.execute(select(func.count(Currency.id)))
    rates = await session.execute(select(func.count(Rate.id)))
    charts = await session.execute(select(func.count(Chart.id)))
    sent = await session.execute(select(func.count(SentChart.id)))
    jobs = await session.execute(select(JobRun).order_by(JobRun.started_at.desc()).limit(10))
    job_list = []
    for j in jobs.scalars().all():
        job_list.append({
            "id": j.id,
            "job_name": j.job_name,
            "status": j.status,
            "started_at": j.started_at.isoformat() if j.started_at else None,
            "finished_at": j.finished_at.isoformat() if j.finished_at else None,
            "duration_ms": j.duration_ms,
        })
    return {
        "currencies": currencies.scalar() or 0,
        "rates": rates.scalar() or 0,
        "charts_total": charts.scalar() or 0,
        "charts_sent": sent.scalar() or 0,
        "recent_jobs": job_list,
    }


@router.get("/status/jobs")
async def jobs_list(limit: int = 50, session: AsyncSession = Depends(get_session)):
    res = await session.execute(select(JobRun).order_by(JobRun.started_at.desc()).limit(limit))
    out = []
    for j in res.scalars().all():
        out.append({
            "id": j.id,
            "job_name": j.job_name,
            "status": j.status,
            "started_at": j.started_at.isoformat() if j.started_at else None,
            "finished_at": j.finished_at.isoformat() if j.finished_at else None,
            "duration_ms": j.duration_ms,
            "details_json": j.details_json,
            "error_text": j.error_text,
        })
    return out
