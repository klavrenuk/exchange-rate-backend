from datetime import datetime

from unittest.mock import AsyncMock

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.models import Chart, SentChart
from app.services.iea import sender as iea_sender


async def _make_chart(session: AsyncSession, url: str, slug: str, downloaded: bool = True):
    chart = Chart(
        url=url,
        slug=slug,
        title=slug,
        discovered_at=datetime.utcnow(),
        downloaded_at=datetime.utcnow() if downloaded else None,
        has_files=downloaded,
    )
    session.add(chart)
    await session.commit()
    return chart


async def test_send_new_charts_skips_already_sent(session, monkeypatch):
    chart = await _make_chart(session, "https://www.iea.org/charts/test-1", "test-1")
    session.add(SentChart(chart_id=chart.id, sent_at=datetime.utcnow(), email_to="to@example.com"))
    await session.commit()

    mock_send = AsyncMock()
    monkeypatch.setattr(iea_sender, "send_email", mock_send)

    await iea_sender.send_new_charts(session)

    mock_send.assert_not_awaited()


async def test_send_new_charts_sends_only_new_and_marks_sent(session, monkeypatch):
    sent_chart = await _make_chart(session, "https://www.iea.org/charts/test-2", "test-2")
    session.add(SentChart(chart_id=sent_chart.id, sent_at=datetime.utcnow(), email_to="to@example.com"))
    await session.commit()

    new_chart = await _make_chart(session, "https://www.iea.org/charts/test-3", "test-3")

    mock_send = AsyncMock()
    monkeypatch.setattr(iea_sender, "send_email", mock_send)

    await iea_sender.send_new_charts(session)

    assert mock_send.await_count == 1
    args, kwargs = mock_send.await_args
    assert "test-3" in args[0]

    sent_res = await session.execute(select(SentChart).where(SentChart.chart_id == new_chart.id))
    assert sent_res.scalar_one_or_none() is not None
