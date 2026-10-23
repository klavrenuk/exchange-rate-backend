from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List
import os


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    APP_ENV: str = "dev"
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000

    DATABASE_URL: str = "sqlite+aiosqlite:///./data/db.sqlite3"

    DATA_DIR: str = "./data"
    REPORT_DIR: str = "./data/reports"
    CHART_DIR: str = "./data/charts"

    SCHEDULER_ENABLED: bool = True
    TZ: str = "Europe/Minsk"
    SCHED_NBRB_UPDATE_CRON: str = "0 9 * * *"
    SCHED_REPORT_CRON: str = "0 18 * * *"
    SCHED_IEA_CHECK_CRON: str = "0 10 * * *"

    NBRB_API_BASE: str = "https://api.nbrb.by"
    NBRB_HISTORY_FROM: str = "2000-01-01"
    NBRB_LOAD_BATCH_DAYS: int = 365

    IEA_CATALOG_URL: str = "https://www.iea.org/data-and-statistics/charts"
    IEA_DOWNLOAD_SCREENSHOT: bool = True
    IEA_BROWSER: str = "playwright"

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = True
    SMTP_USE_SSL: bool = False
    MAIL_FROM: str = ""
    MAIL_TO: str = ""
    MAIL_DRY_RUN: bool = True
    MAIL_SUBJECT_PREFIX: str = "[ExchangeRates]"

    LOG_LEVEL: str = "INFO"

    def mail_to_list(self) -> List[str]:
        if not self.MAIL_TO:
            return []
        return [x.strip() for x in self.MAIL_TO.split(",") if x.strip()]

    def ensure_dirs(self):
        for p in [self.DATA_DIR, self.REPORT_DIR, self.CHART_DIR]:
            os.makedirs(p, exist_ok=True)


settings = Settings()
settings.ensure_dirs()
