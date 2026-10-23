import httpx
from app.core.config import settings


class NBRBClient:
    def __init__(self):
        self.base = settings.NBRB_API_BASE
        self.client = httpx.AsyncClient(timeout=60.0, headers={"User-Agent": "exchange-rate-backend/1.0"})

    async def get_currencies(self):
        r = await self.client.get(f"{self.base}/exrates/currencies")
        r.raise_for_status()
        return r.json()

    async def get_rates_ondate(self, ondate: str, periodicity: int = 0):
        params = {"ondate": ondate}
        if periodicity is not None:
            params["periodicity"] = periodicity
        r = await self.client.get(f"{self.base}/exrates/rates", params=params)
        r.raise_for_status()
        return r.json()

    async def get_rates_dynamics(self, cur_id: int, startdate: str, enddate: str):
        r = await self.client.get(f"{self.base}/exrates/rates/dynamics/{cur_id}", params={"startdate": startdate, "enddate": enddate})
        r.raise_for_status()
        return r.json()

    async def close(self):
        await self.client.aclose()
