"""Scraper for direct API endpoints (JSON APIs like Futurepedia).
These are sources that expose structured data via HTTP APIs — easy to crawl,
high signal quality similar to ProductHunt."""
import requests
from typing import List
from datetime import datetime, timezone
from src.scrapers.base import BaseScraper
from src.models.content import ContentItem


class APIEndpointScraper(BaseScraper):
    """Fetches structured data from JSON API endpoints."""
    name = "api_endpoints"
    category = "api_endpoints"

    def __init__(self, sources: List[dict]):
        self.sources = sources
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/146.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.7",
        })

    def fetch(self) -> List[ContentItem]:
        items = []
        for source in self.sources:
            try:
                fetched = self._fetch_source(source)
                items.extend(fetched)
            except Exception as e:
                import sys
                print(f"[WARN] api_endpoints/{source.get('name', '?')}: {e}", file=sys.stderr)
        return items

    def _fetch_source(self, source: dict) -> List[ContentItem]:
        url = source["url"]
        name = source.get("name", url)
        method = source.get("method", "POST").upper()
        headers = source.get("headers", {})
        body = source.get("body", {})
        parser = source.get("parser", "auto")

        # Merge source-specific headers
        req_headers = dict(self.session.headers)
        req_headers.update(headers)

        if method == "GET":
            resp = self.session.get(url, headers=req_headers, timeout=15)
        else:
            resp = self.session.post(url, json=body, headers=req_headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        # Parse based on source config
        if parser == "futurepedia_tools":
            return self._parse_futurepedia_tools(data, name)
        else:
            return self._parse_auto(data, name, source)

    def _parse_futurepedia_tools(self, data: dict, name: str) -> List[ContentItem]:
        """Parse Futurepedia /api/homepage/tools response."""
        items = []
        tools = data.get("tools", data.get("data", data.get("results", []))) if isinstance(data, dict) else data
        if isinstance(tools, dict):
            # Try to find a list inside
            for key in tools:
                if isinstance(tools[key], list):
                    tools = tools[key]
                    break
        if not isinstance(tools, list):
            return items

        for tool in tools[:30]:  # Cap at 30 to avoid noise
            if isinstance(tool, dict):
                title = tool.get("toolName") or tool.get("name") or tool.get("title", "")
                desc = tool.get("toolShortDescription") or tool.get("description") or tool.get("shortDescription", "")
                # Slug can be nested {"_type": "slug", "current": "..."} or a plain string
                raw_slug = tool.get("slug", "")
                if isinstance(raw_slug, dict):
                    slug = raw_slug.get("current", "")
                else:
                    slug = raw_slug
                url = f"https://www.futurepedia.io/tool/{slug}" if slug else None
                pricing = tool.get("pricing") or tool.get("pricingModel", "")
                raw_cats = tool.get("toolCategories") or tool.get("categories") or tool.get("tags") or []
                categories = [
                    c.get("categoryName", c) if isinstance(c, dict) else c
                    for c in raw_cats
                ]

                if not title:
                    continue

                items.append(ContentItem(
                    source=name,
                    category="api_endpoints",
                    title=title,
                    url=url,
                    description=desc[:500] if desc else None,
                    tags=categories if isinstance(categories, list) else [],
                    extra={
                        "pricing": pricing,
                        "source_type": "product_discovery",
                    },
                ))
        return items

    def _parse_auto(self, data, name: str, source: dict) -> List[ContentItem]:
        """Generic parser: tries to extract items from JSON arrays."""
        items_list = data if isinstance(data, list) else data.get("data", data.get("results", data.get("items", [])))
        if not isinstance(items_list, list):
            return []

        items = []
        title_key = source.get("title_key", "name")
        desc_key = source.get("description_key", "description")
        url_key = source.get("url_key", "url")

        for entry in items_list[:30]:
            if not isinstance(entry, dict):
                continue
            title = entry.get(title_key) or entry.get("title") or entry.get("name", "")
            if not title:
                continue
            items.append(ContentItem(
                source=name,
                category="api_endpoints",
                title=str(title),
                url=entry.get(url_key) or entry.get("url"),
                description=(str(entry.get(desc_key, ""))[:500] or None) if entry.get(desc_key) else None,
                extra={"source_type": source.get("source_type", "api")},
            ))
        return items
