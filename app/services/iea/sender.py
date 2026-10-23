import os
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Chart, SentChart, JobRun
from app.services.email.sender import send_email
from app.core.config import settings
import json


async def send_new_charts(session: AsyncSession):
    job = JobRun(job_name="iea.send_new", status="running")
    session.add(job)
    await session.commit()
    await session.refresh(job)
    try:
        # find charts downloaded but not sent
        res = await session.execute(select(Chart).where(Chart.downloaded_at.is_not(None)))
        charts = res.scalars().all()
        sent_count = 0
        for chart in charts:
            res2 = await session.execute(select(SentChart).where(SentChart.chart_id == chart.id))
            if res2.scalar_one_or_none() is not None:
                continue
            # prepare attachments
            attachments = []
            folder = chart.local_path or os.path.join(settings.CHART_DIR, chart.slug)
            if os.path.exists(folder):
                for fname in os.listdir(folder):
                    if fname.endswith(('.png', '.jpg', '.jpeg', '.svg', '.html', '.csv', '.pdf')):
                        attachments.append(os.path.join(folder, fname))
            subject = f"{settings.MAIL_SUBJECT_PREFIX} IEA chart: {chart.slug}"
            body = f"IEA chart\nURL: {chart.url}\nSlug: {chart.slug}\nDownloaded: {chart.downloaded_at}"
            # send one email per chart with attachments if any
            try:
                if attachments:
                    # send with first attachment or all? requirement says "Один график должен отправляться отдельным письмом" - attach files
                    # send with first major file
                    await send_email(subject, body, attachment_path=attachments[0] if attachments else None)
                else:
                    await send_email(subject, body)
                sc = SentChart(chart_id=chart.id, sent_at=datetime.utcnow(), email_to=",".join(settings.mail_to_list()))
                session.add(sc)
                await session.commit()
                sent_count += 1
            except Exception:
                await session.rollback()
                continue
        job.status = "success"
        job.finished_at = datetime.utcnow()
        if job.started_at:
            job.duration_ms = int((job.finished_at - job.started_at).total_seconds() * 1000)
        job.details_json = json.dumps({"sent": sent_count})
        await session.commit()
    except Exception as e:
        job.status = "failed"
        job.finished_at = datetime.utcnow()
        if job.started_at:
            job.duration_ms = int((job.finished_at - job.started_at).total_seconds() * 1000)
        job.error_text = str(e)
        await session.commit()
        raise
