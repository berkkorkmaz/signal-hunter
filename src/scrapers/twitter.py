import os
import sys
import requests
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from urllib.parse import quote
from src.scrapers.base import BaseScraper
from src.models.content import ContentItem


class TwitterScraper(BaseScraper):
    """Scrape X/Twitter using the v2 API with Bearer Token."""
    name = "twitter"
    category = "twitter"

    def __init__(self, handles: List[str], limit: int = 10, hours: int = 48):
        self.handles = handles
        self.limit = limit
        self.cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=hours)
        self.bearer_token = self._load_token()
        self.session = requests.Session()
        if self.bearer_token:
            self.session.headers.update({
                "Authorization": f"Bearer {self.bearer_token}",
                "User-Agent": "DailyKnowledgeBuilder/1.0",
            })

    def _load_token(self) -> Optional[str]:
        """Load Bearer Token from .env file or environment."""
        token = os.environ.get("X_BEARER_TOKEN")
        if token:
            return token
        # Try .env file
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("X_BEARER_TOKEN="):
                        return line.split("=", 1)[1]
        return None

    def fetch(self) -> List[ContentItem]:
        if not self.bearer_token:
            print("[WARN] twitter: no X_BEARER_TOKEN found in .env or environment", file=sys.stderr)
            return []
        items = []
        for handle in self.handles:
            items.extend(self._fetch_handle(handle))
        return items

    def _get_user_id(self, handle: str) -> Optional[str]:
        """Resolve @handle to user ID via X API v2."""
        url = f"https://api.x.com/2/users/by/username/{handle}"
        resp = self.session.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            return data.get("id")
        print(f"[WARN] twitter: could not resolve @{handle}: {resp.status_code} {resp.text[:200]}", file=sys.stderr)
        return None

    def _fetch_handle(self, handle: str) -> List[ContentItem]:
        user_id = self._get_user_id(handle)
        if not user_id:
            return []

        # Fetch recent tweets
        start_time = self.cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")
        url = f"https://api.x.com/2/users/{user_id}/tweets"
        params = {
            "max_results": max(min(self.limit, 100), 5),  # X API minimum is 5
            "start_time": start_time,
            "tweet.fields": "created_at,public_metrics,text",
            "exclude": "retweets,replies",
        }
        resp = self.session.get(url, params=params, timeout=15)
        if resp.status_code != 200:
            print(f"[WARN] twitter: failed to fetch tweets for @{handle}: {resp.status_code} {resp.text[:200]}", file=sys.stderr)
            return []

        data = resp.json()
        tweets = data.get("data", [])
        items = []
        for tweet in tweets:
            metrics = tweet.get("public_metrics", {})
            created = tweet.get("created_at")
            timestamp = datetime.fromisoformat(created.replace("Z", "+00:00")) if created else None
            tweet_id = tweet.get("id", "")

            items.append(ContentItem(
                source=f"@{handle}",
                category="twitter",
                title=tweet["text"][:120],
                url=f"https://x.com/{handle}/status/{tweet_id}",
                description=tweet["text"],
                author=handle,
                timestamp=timestamp,
                score=metrics.get("like_count", 0),
                extra={
                    "retweets": metrics.get("retweet_count", 0),
                    "replies": metrics.get("reply_count", 0),
                    "impressions": metrics.get("impression_count", 0),
                    "tweet_id": tweet_id,
                },
            ))
        return items
