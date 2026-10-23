from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.core.config import settings
from app.tasks import jobs
from app.db.base import AsyncSessionLocal
import pytz


scheduler = AsyncIOScheduler(timezone=pytz.timezone(settings.TZ))


def setup_scheduler():
    if not settings.SCHEDULER_ENABLED:
        return
    # parse cron simple (minute hour day month day_of_week)
    def parse_cron(cron: str):
        parts = cron.split()
        if len(parts) == 5:
            m, h, dom, mon, dow = parts
            return CronTrigger(minute=m, hour=h, day=dom, month=mon, day_of_week=dow)
        return None

    t1 = parse_cron(settings.SCHED_NBRB_UPDATE_CRON)
    if t1:
        scheduler.add_job(jobs.nbrb_update_job, t1, id="nbrb_update")
    t2 = parse_cron(settings.SCHED_REPORT_CRON)
    if t2:
        scheduler.add_job(jobs.nbrb_report_job, t2, id="nbrb_report")
    t3 = parse_cron(settings.SCHED_IEA_CHECK_CRON)
    if t3:
        scheduler.add_job(jobs.iea_check_job, t3, id="iea_check")


async def start_scheduler():
    if not scheduler.running:
        setup_scheduler()
        scheduler.start()


async def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown()
