import os
import re
from urllib.parse import urlparse
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Chart, JobRun
from app.services.iea.parser import IEAParser
from app.core.config import settings
import json


async def discover_charts(session: AsyncSession):
    job = JobRun(job_name="iea.discover", status="running")
    session.add(job)
    await session.commit()
    await session.refresh(job)
    parser = IEAParser()
    try:
        links = await parser.get_catalog_links()
        new_count = 0
        for url in links:
            res = await session.execute(select(Chart).where(Chart.url == url))
            if res.scalar_one_or_none() is not None:
                continue
            parsed = urlparse(url)
            slug = parsed.path.rstrip('/').split('/')[-1]
            chart = Chart(url=url, slug=slug, discovered_at=datetime.utcnow())
            session.add(chart)
            new_count += 1
        await session.commit()
        job.status = "success"
        job.finished_at = datetime.utcnow()
        if job.started_at:
            job.duration_ms = int((job.finished_at - job.started_at).total_seconds() * 1000)
        job.details_json = json.dumps({"discovered": len(links), "new": new_count})
        await session.commit()
    except Exception as e:
        job.status = "failed"
        job.finished_at = datetime.utcnow()
        if job.started_at:
            job.duration_ms = int((job.finished_at - job.started_at).total_seconds() * 1000)
        job.error_text = str(e)
        await session.commit()
        raise
    finally:
        await parser.close()


async def download_new_charts(session: AsyncSession):
    job = JobRun(job_name="iea.download_new", status="running")
    session.add(job)
    await session.commit()
    await session.refresh(job)
    parser = IEAParser()
    try:
        res = await session.execute(select(Chart).where(Chart.downloaded_at.is_(None)))
        charts = res.scalars().all()
        downloaded = 0
        for chart in charts:
            try:
                os.makedirs(os.path.join(settings.CHART_DIR, chart.slug), exist_ok=True)
                html = await parser.get_chart_page(chart.url)
                html_path = os.path.join(settings.CHART_DIR, chart.slug, "page.html")
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html)
                # try to save csv if present in data-chart-csv
                m = re.search(r'data-chart-csv="([^"]+)"', html)
                if m:
                    csv_path = os.path.join(settings.CHART_DIR, chart.slug, "data.csv")
                    # unescape
                    csv_data = m.group(1).replace('&quot;', '"').replace('\\n', '\n')
                    with open(csv_path, 'w', encoding='utf-8') as f:
                        f.write(csv_data)
                # try screenshot with playwright if enabled
                if settings.IEA_DOWNLOAD_SCREENSHOT:
                    try:
                        from playwright.async_api import async_playwright
                        async with async_playwright() as p:
                            browser = await p.chromium.launch(headless=True)
                            page = await browser.new_page()
                            await page.goto(chart.url, wait_until="networkidle", timeout=60000)
                            png_path = os.path.join(settings.CHART_DIR, chart.slug, "screenshot.png")
                            await page.screenshot(path=png_path, full_page=True)
                            await browser.close()
                    except Exception:
                        pass
                chart.downloaded_at = datetime.utcnow()
                chart.has_files = True
                chart.local_path = os.path.join(settings.CHART_DIR, chart.slug)
                downloaded += 1
            except Exception:
                continue
        await session.commit()
        job.status = "success"
        job.finished_at = datetime.utcnow()
        if job.started_at:
            job.duration_ms = int((job.finished_at - job.started_at).total_seconds() * 1000)
        job.details_json = json.dumps({"downloaded": downloaded})
        await session.commit()
    except Exception as e:
        job.status = "failed"
        job.finished_at = datetime.utcnow()
        if job.started_at:
            job.duration_ms = int((job.finished_at - job.started_at).total_seconds() * 1000)
        job.error_text = str(e)
        await session.commit()
        raise
    finally:
        await parser.close()
