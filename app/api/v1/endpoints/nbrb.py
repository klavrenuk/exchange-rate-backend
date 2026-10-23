from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.deps import get_session
from app.services.nbrb import loader, report

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
