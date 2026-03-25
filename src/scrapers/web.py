import sys
import requests
from typing import List
from bs4 import BeautifulSoup
from src.scrapers.base import BaseScraper
from src.models.content import ContentItem

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


class WebScraper(BaseScraper):
    """Generic web scraper for data sources that need browser-like headers."""
    name = "web"
    category = "data_sources"

    def __init__(self, sources: List[dict]):
        self.sources = sources
        self.session = requests.Session()
        self.session.headers.update(BROWSER_HEADERS)

    def fetch(self) -> List[ContentItem]:
        items = []
        for source in self.sources:
            try:
                url = source["url"]
                name = source.get("name", url)
                resp = self.session.get(url, timeout=15)
                resp.raise_for_status()
                parsed = self._parse_generic(resp.text, url, name)
                items.extend(parsed)
                print(f"[OK] web/{name}: {len(parsed)} items", file=sys.stderr)
            except Exception as e:
                print(f"[WARN] web/{source.get('name', '?')}: {e}", file=sys.stderr)
        return items

    def _parse_generic(self, html: str, base_url: str, name: str) -> List[ContentItem]:
        """Extract links and titles from a page."""
        soup = BeautifulSoup(html, "html.parser")
        items = []
        seen_urls = set()

        # Look for article-like elements
        for el in soup.select("a[href]"):
            href = el.get("href", "")
            text = el.get_text(strip=True)
            if not text or len(text) < 10 or len(text) > 300:
                continue
            # Make absolute URL
            if href.startswith("/"):
                from urllib.parse import urljoin
                href = urljoin(base_url, href)
            elif not href.startswith("http"):
                continue
            if href in seen_urls:
                continue
            seen_urls.add(href)
            items.append(ContentItem(
                source=name,
                category="data_sources",
                title=text,
                url=href,
            ))
        return items
