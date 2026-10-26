import os
from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.models import Currency, Rate
from app.core.config import settings
from app.services.nbrb import report as nbrb_report


async def _make_currency_with_rate(session: AsyncSession, cur_id_nbrb: int, abbr: str, rate: float):
    cur = Currency(cur_id_nbrb=cur_id_nbrb, abbreviation=abbr, code=abbr, name=f"{abbr} currency")
    session.add(cur)
    await session.commit()
    r = Rate(
        currency_id=cur.id,
        date=date.today(),
        rate=rate,
        scale=1,
        cur_abbreviation=abbr,
        cur_id_nbrb=cur_id_nbrb,
    )
    session.add(r)
    await session.commit()
    return cur, r


async def test_rate_has_unique_constraint_per_currency_and_date(session: AsyncSession):
    cur, _ = await _make_currency_with_rate(session, 1, "USD", 1.0)

    dup_rate = Rate(
        currency_id=cur.id,
        date=date.today(),
        rate=2.0,
        scale=1,
        cur_abbreviation="USD",
        cur_id_nbrb=1,
    )
    session.add(dup_rate)
    with pytest.raises(IntegrityError):
        await session.commit()


async def test_generate_excel_report_creates_file(session: AsyncSession, monkeypatch, tmp_path):
    await _make_currency_with_rate(session, 2, "EUR", 1.05)
    monkeypatch.setattr(settings, "REPORT_DIR", str(tmp_path))
    path = await nbrb_report.generate_excel_report(session, report_date=date.today())
    assert path.endswith(".xlsx")
    assert os.path.exists(path)
