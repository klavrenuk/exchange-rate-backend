from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Boolean, UniqueConstraint, Index, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class Currency(Base):
    __tablename__ = "currencies"

    id = Column(Integer, primary_key=True)
    cur_id_nbrb = Column(Integer, unique=True, index=True)
    code = Column(String(10))
    abbreviation = Column(String(10), index=True)
    name = Column(String(255))
    name_eng = Column(String(255))
    scale = Column(Integer, default=1)
    periodicity = Column(Integer, default=0)
    date_start = Column(Date)
    date_end = Column(Date)
    parent_id = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    rates = relationship("Rate", back_populates="currency")


class Rate(Base):
    __tablename__ = "rates"
    __table_args__ = (
        UniqueConstraint("currency_id", "date", name="uq_rate_currency_date"),
        Index("ix_rates_date", "date"),
    )

    id = Column(Integer, primary_key=True)
    currency_id = Column(Integer, ForeignKey("currencies.id"), index=True)
    date = Column(Date, index=True)
    rate = Column(Float)
    scale = Column(Integer)
    cur_abbreviation = Column(String(10))
    cur_id_nbrb = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    currency = relationship("Currency", back_populates="rates")


class Chart(Base):
    __tablename__ = "charts"

    id = Column(Integer, primary_key=True)
    url = Column(String(512), unique=True, index=True)
    slug = Column(String(255), index=True)
    title = Column(String(512))
    discovered_at = Column(DateTime(timezone=True), server_default=func.now())
    downloaded_at = Column(DateTime(timezone=True))
    last_checked_at = Column(DateTime(timezone=True))
    local_path = Column(String(1024))
    has_files = Column(Boolean, default=False)


class SentChart(Base):
    __tablename__ = "sent_charts"
    __table_args__ = (
        UniqueConstraint("chart_id", name="uq_sent_chart"),
    )

    id = Column(Integer, primary_key=True)
    chart_id = Column(Integer, ForeignKey("charts.id"), index=True)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    email_to = Column(String(512))
    message_id = Column(String(255))


class JobRun(Base):
    __tablename__ = "job_runs"

    id = Column(Integer, primary_key=True)
    job_name = Column(String(64), index=True)
    status = Column(String(32), index=True)  # running/success/failed/skipped
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True))
    duration_ms = Column(Integer)
    details_json = Column(Text)
    error_text = Column(Text)


class TaskState(Base):
    __tablename__ = "task_state"
    __table_args__ = (
        UniqueConstraint("key", name="uq_task_state_key"),
    )

    id = Column(Integer, primary_key=True)
    key = Column(String(128), index=True)
    value_json = Column(Text)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
