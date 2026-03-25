import requests
from typing import List
from datetime import datetime, timezone
from src.scrapers.base import BaseScraper
from src.models.content import ContentItem


class RedditScraper(BaseScraper):
    name = "reddit"
    category = "reddit"

    def __init__(self, subreddits: List[str], limit: int = 10, sort: str = "top", time_filter: str = "day"):
        self.subreddits = subreddits
        self.limit = limit
        self.sort = sort  # "top", "hot", "new", "rising"
        self.time_filter = time_filter  # "day", "week", "month" (for top sort)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "DailyKnowledgeBuilder/1.0 (knowledge aggregation bot)"
        })

    def fetch(self) -> List[ContentItem]:
        items = []
        for sub in self.subreddits:
            items.extend(self._fetch_subreddit(sub))
        return items

    def _fetch_subreddit(self, subreddit: str) -> List[ContentItem]:
        url = f"https://www.reddit.com/r/{subreddit}/{self.sort}.json?limit={self.limit}&t={self.time_filter}"
        resp = self.session.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        items = []
        for post in data.get("data", {}).get("children", []):
            d = post.get("data", {})
            if d.get("stickied"):
                continue
            items.append(ContentItem(
                source=f"r/{subreddit}",
                category="reddit",
                title=d.get("title", ""),
                url=f"https://reddit.com{d.get('permalink', '')}",
                description=d.get("selftext", "")[:500] if d.get("selftext") else None,
                score=d.get("score"),
                author=d.get("author"),
                timestamp=datetime.fromtimestamp(d.get("created_utc", 0), tz=timezone.utc),
                extra={
                    "num_comments": d.get("num_comments", 0),
                    "link_url": d.get("url", ""),
                    "subreddit": subreddit,
                },
            ))
        return items
