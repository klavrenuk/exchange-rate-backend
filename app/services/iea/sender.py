import os
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.common.models import Chart, SentChart, JobRun
from app.services.email.sender import send_email
from app.core.config import settings
import json


async def send_new_charts(session: AsyncSession):
    job = JobRun(job_name="iea.send_new", status="running")
    session.add(job)
    await session.commit()
    await session.refresh(job)
    try:
        res = await session.execute(select(Chart).where(Chart.downloaded_at.is_not(None)))
        charts = [
            {
                "id": chart.id,
                "url": chart.url,
                "slug": chart.slug,
                "downloaded_at": chart.downloaded_at,
                "local_path": chart.local_path,
            }
            for chart in res.scalars().all()
        ]
        sent_count = 0
        failed_count = 0
        for chart in charts:
            res2 = await session.execute(select(SentChart).where(SentChart.chart_id == chart["id"]))
            if res2.scalar_one_or_none() is not None:
                continue
            attachments = []
            folder = chart["local_path"] or os.path.join(settings.CHART_DIR, chart["slug"])
            if os.path.exists(folder):
                for fname in os.listdir(folder):
                    if fname.endswith(('.png', '.jpg', '.jpeg', '.svg', '.html', '.csv', '.pdf')):
                        attachments.append(os.path.join(folder, fname))
            subject = f"{settings.MAIL_SUBJECT_PREFIX} IEA chart: {chart['slug']}"
            body = f"IEA chart\nURL: {chart['url']}\nSlug: {chart['slug']}\nDownloaded: {chart['downloaded_at']}"
            try:
                if attachments:
                    await send_email(subject, body, attachment_path=attachments[0])
                else:
                    await send_email(subject, body)
            except Exception:
                failed_count += 1
                continue
            try:
                session.add(
                    SentChart(
                        chart_id=chart["id"],
                        sent_at=datetime.utcnow(),
                        email_to=",".join(settings.mail_to_list()),
                    )
                )
                await session.commit()
                sent_count += 1
            except Exception:
                await session.rollback()
                await session.refresh(job)
                failed_count += 1
                continue
        job.status = "success"
        job.finished_at = datetime.utcnow()
        if job.started_at:
            job.duration_ms = int((job.finished_at - job.started_at).total_seconds() * 1000)
        job.details_json = json.dumps({"sent": sent_count, "failed": failed_count})
        await session.commit()
    except Exception as e:
        job.status = "failed"
        job.finished_at = datetime.utcnow()
        if job.started_at:
            job.duration_ms = int((job.finished_at - job.started_at).total_seconds() * 1000)
        job.error_text = str(e)
        await session.commit()
        raise
