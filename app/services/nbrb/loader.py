import json
from datetime import date, datetime, timedelta
from typing import Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Currency, Rate, JobRun, TaskState
from app.services.nbrb.client import NBRBClient
from app.core.config import settings


async def log_job_start(session: AsyncSession, job_name: str):
    job = JobRun(job_name=job_name, status="running")
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job


async def log_job_end(session: AsyncSession, job: JobRun, status: str, details: dict = None, error_text: str = None):
    job.status = status
    job.finished_at = datetime.utcnow()
    if job.started_at:
        job.duration_ms = int((job.finished_at - job.started_at).total_seconds() * 1000)
    if details is not None:
        job.details_json = json.dumps(details, ensure_ascii=False)
    if error_text is not None:
        job.error_text = error_text
    await session.commit()


async def sync_currencies(session: AsyncSession):
    job = await log_job_start(session, "nbrb.sync_currencies")
    client = NBRBClient()
    try:
        data = await client.get_currencies()
        today = date.today()
        count_new = 0
        count_upd = 0
        for c in data:
            cur_id = c.get("Cur_ID")
            res = await session.execute(select(Currency).where(Currency.cur_id_nbrb == cur_id))
            cur = res.scalar_one_or_none()
            ds = None
            de = None
            try:
                if c.get("Cur_DateStart"):
                    ds = datetime.fromisoformat(c["Cur_DateStart"].replace("Z", "+00:00")).date()
            except Exception:
                pass
            try:
                if c.get("Cur_DateEnd"):
                    de = datetime.fromisoformat(c["Cur_DateEnd"].replace("Z", "+00:00")).date()
            except Exception:
                pass
            if cur is None:
                cur = Currency(
                    cur_id_nbrb=cur_id,
                    code=c.get("Cur_Code"),
                    abbreviation=c.get("Cur_Abbreviation"),
                    name=c.get("Cur_Name"),
                    name_eng=c.get("Cur_Name_Eng"),
                    scale=c.get("Cur_Scale") or 1,
                    periodicity=c.get("Cur_Periodicity") or 0,
                    date_start=ds,
                    date_end=de,
                    parent_id=c.get("Cur_ParentID"),
                )
                session.add(cur)
                count_new += 1
            else:
                cur.code = c.get("Cur_Code")
                cur.abbreviation = c.get("Cur_Abbreviation")
                cur.name = c.get("Cur_Name")
                cur.name_eng = c.get("Cur_Name_Eng")
                cur.scale = c.get("Cur_Scale") or cur.scale
                cur.periodicity = c.get("Cur_Periodicity") or cur.periodicity
                cur.date_start = ds or cur.date_start
                cur.date_end = de or cur.date_end
                cur.parent_id = c.get("Cur_ParentID") or cur.parent_id
                count_upd += 1
        await session.commit()
        await log_job_end(session, job, "success", {"new": count_new, "updated": count_upd, "total": len(data)})
    except Exception as e:
        await log_job_end(session, job, "failed", error_text=str(e))
        raise
    finally:
        await client.close()


async def update_today(session: AsyncSession, periodicity: int = 0):
    job = await log_job_start(session, "nbrb.update_today")
    client = NBRBClient()
    try:
        today = date.today()
        data = await client.get_rates_ondate(today.isoformat(), periodicity=periodicity)
        inserted = 0
        skipped = 0
        for item in data:
            cur_id = item.get("Cur_ID")
            res = await session.execute(select(Currency).where(Currency.cur_id_nbrb == cur_id))
            cur = res.scalar_one_or_none()
            if cur is None:
                continue
            d = datetime.fromisoformat(item["Date"].replace("Z", "+00:00")).date()
            res2 = await session.execute(select(Rate).where(and_(Rate.currency_id == cur.id, Rate.date == d)))
            exists = res2.scalar_one_or_none()
            if exists is not None:
                skipped += 1
                continue
            rate = Rate(
                currency_id=cur.id,
                date=d,
                rate=float(item.get("Cur_OfficialRate")),
                scale=item.get("Cur_Scale") or cur.scale,
                cur_abbreviation=item.get("Cur_Abbreviation") or cur.abbreviation,
                cur_id_nbrb=cur_id,
            )
            session.add(rate)
            inserted += 1
        await session.commit()
        await log_job_end(session, job, "success", {"inserted": inserted, "skipped": skipped, "total": len(data), "date": today.isoformat()})
    except Exception as e:
        await log_job_end(session, job, "failed", error_text=str(e))
        raise
    finally:
        await client.close()


async def load_history(session: AsyncSession, cur_abbr: Optional[str] = None, from_date: Optional[str] = None, to_date: Optional[str] = None):
    job = await log_job_start(session, "nbrb.load_history")
    client = NBRBClient()
    try:
        if from_date is None:
            from_date = settings.NBRB_HISTORY_FROM
        if to_date is None:
            to_date = date.today().isoformat()
        fd = datetime.strptime(from_date, "%Y-%m-%d").date()
        td = datetime.strptime(to_date, "%Y-%m-%d").date()
        q = select(Currency)
        if cur_abbr:
            q = q.where(Currency.abbreviation == cur_abbr.upper())
        res = await session.execute(q)
        currencies = res.scalars().all()
        total_inserted = 0
        for cur in currencies:
            if cur.cur_id_nbrb is None:
                continue
            if cur.date_end and cur.date_end < fd:
                continue
            s = fd
            if cur.date_start and cur.date_start > s:
                s = cur.date_start
            if td < s:
                continue
            # load in chunks
            cur_s = s
            while cur_s <= td:
                cur_e = min(cur_s + timedelta(days=settings.NBRB_LOAD_BATCH_DAYS - 1), td)
                try:
                    data = await client.get_rates_dynamics(cur.cur_id_nbrb, cur_s.isoformat(), cur_e.isoformat())
                except Exception as ex:
                    # log and continue
                    cur_s = cur_e + timedelta(days=1)
                    continue
                for item in data:
                    d = datetime.fromisoformat(item["Date"].replace("Z", "+00:00")).date()
                    res2 = await session.execute(select(Rate).where(and_(Rate.currency_id == cur.id, Rate.date == d)))
                    if res2.scalar_one_or_none() is not None:
                        continue
                    rate = Rate(
                        currency_id=cur.id,
                        date=d,
                        rate=float(item.get("Cur_OfficialRate")),
                        scale=item.get("Cur_Scale") or cur.scale,
                        cur_abbreviation=cur.abbreviation,
                        cur_id_nbrb=cur.cur_id_nbrb,
                    )
                    session.add(rate)
                    total_inserted += 1
                await session.commit()
                cur_s = cur_e + timedelta(days=1)
        await log_job_end(session, job, "success", {"inserted": total_inserted, "from": fd.isoformat(), "to": td.isoformat()})
    except Exception as e:
        await log_job_end(session, job, "failed", error_text=str(e))
        raise
    finally:
        await client.close()
