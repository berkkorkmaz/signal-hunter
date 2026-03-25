"""Historical data store with daily dedup.

Stores all fetched data organized by date, so you can look back at trends over time.
Also prevents re-fetching the same source on the same day to reduce API costs.

Structure:
  .cache/
    2026-03-25/
      reddit.json
      twitter.json
      youtube.json
      app_stores.json
    2026-03-26/
      ...
"""
import json
import os
from datetime import date
from typing import List, Optional
from src.models.content import ContentItem

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".cache")


def _day_dir(day: str = None) -> str:
    day = day or str(date.today())
    return os.path.join(CACHE_DIR, day)


def _source_path(source_key: str, day: str = None) -> str:
    return os.path.join(_day_dir(day), f"{source_key}.json")


def is_cached(source_key: str) -> bool:
    """Check if a source was already fetched today."""
    return os.path.exists(_source_path(source_key))


def get_cached(source_key: str, day: str = None) -> Optional[List[ContentItem]]:
    """Get cached items for a source. Defaults to today, or specify a date like '2026-03-25'."""
    path = _source_path(source_key, day)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        items_data = json.load(f)
    return [ContentItem(**item) for item in items_data]


def save_to_cache(source_key: str, items: List[ContentItem]):
    """Save fetched items to today's date folder."""
    day_path = _day_dir()
    os.makedirs(day_path, exist_ok=True)
    path = _source_path(source_key)
    with open(path, "w") as f:
        json.dump([item.model_dump(mode="json") for item in items], f, indent=2, default=str)


def get_history(source_key: str, days: int = 7) -> dict:
    """Get cached items for a source across the last N days. Returns {date: [items]}."""
    from datetime import timedelta
    today = date.today()
    history = {}
    for i in range(days):
        day = str(today - timedelta(days=i))
        items = get_cached(source_key, day)
        if items:
            history[day] = items
    return history


def list_cached_days() -> List[str]:
    """List all dates that have cached data."""
    if not os.path.exists(CACHE_DIR):
        return []
    days = [d for d in sorted(os.listdir(CACHE_DIR)) if os.path.isdir(os.path.join(CACHE_DIR, d))]
    return days


def clear_cache(day: str = None):
    """Clear cache for a specific day, or all if day is None."""
    import shutil
    if day:
        path = _day_dir(day)
        if os.path.exists(path):
            shutil.rmtree(path)
    else:
        if os.path.exists(CACHE_DIR):
            shutil.rmtree(CACHE_DIR)
