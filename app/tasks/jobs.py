from app.db.base import AsyncSessionLocal
from app.services.nbrb import loader, report
from app.services.iea import downloader, sender


async def nbrb_update_job():
    async with AsyncSessionLocal() as session:
        try:
            await loader.sync_currencies(session)
        except Exception:
            pass
        try:
            await loader.update_today(session, periodicity=0)
        except Exception:
            pass


async def nbrb_report_job():
    async with AsyncSessionLocal() as session:
        try:
            await report.report_and_send(session)
        except Exception:
            pass


async def iea_check_job():
    async with AsyncSessionLocal() as session:
        try:
            await downloader.discover_charts(session)
        except Exception:
            pass
        try:
            await downloader.download_new_charts(session)
        except Exception:
            pass
        try:
            await sender.send_new_charts(session)
        except Exception:
            pass


async def run_all_manual():
    await nbrb_update_job()
    try:
        from app.db.base import AsyncSessionLocal
        from app.services.nbrb import report
        async with AsyncSessionLocal() as session:
            try:
                await report.report_and_send(session)
            except Exception:
                pass
    except Exception:
        pass
    await iea_check_job()
