import httpx
from bs4 import BeautifulSoup
from app.core.config import settings
import re


class IEAParser:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0, headers={"User-Agent": "exchange-rate-backend/1.0", "Accept-Language": "en-US,en;q=0.9"}, follow_redirects=True)

    async def get_catalog_links(self):
        r = await self.client.get(settings.IEA_CATALOG_URL)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'lxml')
        links = set()
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/data-and-statistics/charts/' in href and href.count('/') >= 4:
                if href.startswith('http'):
                    links.add(href)
                else:
                    links.add(f"https://www.iea.org{href}")
        # also look for data-chart links
        for m in re.findall(r'href="(/data-and-statistics/charts/[a-z0-9\-]+)"', r.text):
            links.add(f"https://www.iea.org{m}")
        return sorted(list(links))

    async def get_chart_page(self, url: str):
        r = await self.client.get(url)
        r.raise_for_status()
        return r.text

    async def close(self):
        await self.client.aclose()
