from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.deps import get_session
from app.services.nbrb import loader, report
from app.common.models import Rate, Currency
from datetime import date, datetime

router = APIRouter()


@router.post("/sync-currencies")
async def sync_currencies(session: AsyncSession = Depends(get_session)):
    await loader.sync_currencies(session)
    return {"status": "ok"}


@router.post("/load-history")
async def load_history(cur_abbr: str = Query(None), from_date: str = Query(None), to_date: str = Query(None), session: AsyncSession = Depends(get_session)):
    await loader.load_history(session, cur_abbr=cur_abbr, from_date=from_date, to_date=to_date)
    return {"status": "ok"}


@router.post("/update-today")
async def update_today(periodicity: int = 0, session: AsyncSession = Depends(get_session)):
    await loader.update_today(session, periodicity=periodicity)
    return {"status": "ok"}


@router.post("/report-and-send")
async def report_and_send(session: AsyncSession = Depends(get_session)):
    path = await report.report_and_send(session)
    return {"status": "ok", "path": path}


@router.get("/rates")
async def get_rates(ondate: str = Query(None), session: AsyncSession = Depends(get_session)):
    if ondate is None:
        ondate = date.today().isoformat()
    try:
        dt = datetime.strptime(ondate, "%Y-%m-%d").date()
    except Exception:
        dt = date.today()
    q = select(Rate, Currency).join(Currency, Rate.currency_id == Currency.id).where(Rate.date == dt).order_by(Currency.abbreviation)
    res = await session.execute(q)
    out = []
    for rate, cur in res.all():
        out.append({
            "date": rate.date.isoformat() if rate.date else dt.isoformat(),
            "currency_id": cur.id,
            "abbreviation": cur.abbreviation,
            "name": cur.name,
            "code": cur.code,
            "scale": rate.scale or cur.scale,
            "rate": rate.rate,
        })
    return out
