"""Main collector: runs all Python scrapers and outputs JSON.
Uses daily cache to avoid re-fetching sources already collected today."""
import json
import sys
import os
import yaml
from typing import List
from src.models.content import ContentItem
from src.cache import is_cached, get_cached, save_to_cache


def load_config() -> dict:
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")
    with open(config_path) as f:
        return yaml.safe_load(f)


def _collect_with_cache(source_key: str, fetch_fn, force: bool = False) -> List[ContentItem]:
    """Fetch from source, using cache if already fetched today."""
    if not force and is_cached(source_key):
        cached = get_cached(source_key)
        if cached is not None:
            print(f"[CACHE] {source_key}: {len(cached)} items (already fetched today)", file=sys.stderr)
            return cached
    items = fetch_fn()
    save_to_cache(source_key, items)
    return items


def collect_reddit(config: dict, force: bool = False) -> List[ContentItem]:
    from src.scrapers.reddit import RedditScraper
    subs = [s["subreddit"] for s in config.get("sources", {}).get("reddit", [])]
    if not subs:
        return []
    return _collect_with_cache("reddit", lambda: RedditScraper(subs).safe_fetch(), force)


def collect_youtube(config: dict, force: bool = False) -> List[ContentItem]:
    from src.scrapers.youtube import YouTubeScraper
    channels = config.get("sources", {}).get("youtube", [])
    if not channels:
        return []
    return _collect_with_cache("youtube", lambda: YouTubeScraper(channels, hours=48, fetch_transcripts=True).safe_fetch(), force)


def collect_twitter(config: dict, force: bool = False) -> List[ContentItem]:
    from src.scrapers.twitter import TwitterScraper
    handles = [h["handle"] for h in config.get("sources", {}).get("twitter", [])]
    if not handles:
        return []
    return _collect_with_cache("twitter", lambda: TwitterScraper(handles, limit=100).safe_fetch(), force)


def collect_app_stores(config: dict, force: bool = False) -> List[ContentItem]:
    from src.scrapers.app_stores import PlaywrightScraper
    sources = config.get("sources", {}).get("app_stores", [])
    if not sources:
        return []
    return _collect_with_cache("app_stores", lambda: PlaywrightScraper(sources).safe_fetch(), force)


def collect_api_endpoints(config: dict, force: bool = False) -> List[ContentItem]:
    from src.scrapers.api_endpoints import APIEndpointScraper
    sources = config.get("sources", {}).get("api_endpoints", [])
    if not sources:
        return []
    return _collect_with_cache("api_endpoints", lambda: APIEndpointScraper(sources).safe_fetch(), force)


def collect_all(categories: List[str] = None, force: bool = False) -> List[ContentItem]:
    """Run all scrapers (or specific categories) and return items.
    Uses daily cache unless force=True."""
    config = load_config()
    all_items = []

    collectors = {
        "reddit": collect_reddit,
        "youtube": collect_youtube,
        "twitter": collect_twitter,
        "app_stores": collect_app_stores,
        "api_endpoints": collect_api_endpoints,
    }

    for name, collector_fn in collectors.items():
        if categories and name not in categories:
            continue
        items = collector_fn(config, force=force)
        all_items.extend(items)

    return all_items


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Daily Knowledge Builder - Collector")
    parser.add_argument("--test", type=str, help="Test a specific category (reddit, youtube, twitter, app_stores, api_endpoints)")
    parser.add_argument("--force", action="store_true", help="Ignore cache and re-fetch all sources")
    parser.add_argument("--date", type=str, default=None, help="Target date (YYYY-MM-DD). Defaults to yesterday. Use 'today' for today.")
    args = parser.parse_args()

    if args.date:
        from src.cache import set_target_date
        set_target_date(args.date)

    categories = [args.test] if args.test else None
    items = collect_all(categories, force=args.force)

    # Output as JSON
    output = [item.model_dump(mode="json") for item in items]
    json.dump(output, sys.stdout, indent=2, default=str)
    print(f"\n\n# Total: {len(items)} items collected", file=sys.stderr)


if __name__ == "__main__":
    main()
