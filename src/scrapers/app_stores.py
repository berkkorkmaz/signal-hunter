import sys
from typing import List
from src.scrapers.base import BaseScraper
from src.models.content import ContentItem


class PlaywrightScraper(BaseScraper):
    """Scraper for JS-heavy sites using Playwright headless browser.
    Used for AppMagic, AppRaven, NeonRev, and any other JS-rendered pages.
    """
    name = "playwright"
    category = "app_stores"

    def __init__(self, sources: List[dict]):
        self.sources = sources

    def fetch(self) -> List[ContentItem]:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("[WARN] playwright: not installed", file=sys.stderr)
            return []

        items = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            for source in self.sources:
                try:
                    page = context.new_page()
                    url = source["url"]
                    name = source.get("name", url)
                    page.goto(url, wait_until="networkidle", timeout=30000)
                    # Wait for content to render
                    page.wait_for_timeout(3000)
                    parsed = self._extract_content(page, url, name)
                    items.extend(parsed)
                    print(f"[OK] playwright/{name}: {len(parsed)} items", file=sys.stderr)
                    page.close()
                except Exception as e:
                    print(f"[WARN] playwright/{source.get('name', '?')}: {e}", file=sys.stderr)
            browser.close()
        return items

    def _extract_content(self, page, base_url: str, name: str) -> List[ContentItem]:
        """Extract meaningful content from the rendered page."""
        items = []
        seen = set()

        # Get all links with visible text
        links = page.evaluate("""() => {
            const results = [];
            document.querySelectorAll('a[href]').forEach(a => {
                const text = a.innerText?.trim();
                const href = a.href;
                if (text && text.length > 5 && text.length < 300 && href.startsWith('http')) {
                    results.push({text, href});
                }
            });
            return results;
        }""")

        for link in links:
            if link["href"] in seen:
                continue
            seen.add(link["href"])
            # Filter out navigation/footer links
            text = link["text"]
            if any(skip in text.lower() for skip in ["privacy", "terms", "cookie", "login", "sign"]):
                continue
            items.append(ContentItem(
                source=name,
                category="app_stores",
                title=text[:200],
                url=link["href"],
            ))
        return items
