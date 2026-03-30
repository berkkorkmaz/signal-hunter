"""Scoring engine: normalize scores across sources, detect cross-source signals,
track velocity across days, and factor in newsletter mentions."""
import json
import os
import re
import string
import sys
import yaml
from collections import defaultdict
from datetime import date, timedelta
from typing import List, Optional
from src.cache import get_history, get_cached, list_cached_days, get_target_date
from src.models.content import ContentItem

STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "can", "shall", "to", "of", "in", "for",
    "on", "with", "at", "by", "from", "as", "into", "about", "between",
    "through", "after", "before", "above", "below", "and", "but", "or",
    "not", "no", "so", "if", "then", "than", "too", "very", "just",
    "that", "this", "it", "its", "i", "we", "you", "he", "she", "they",
    "what", "which", "who", "how", "when", "where", "why", "all", "each",
    "new", "now", "up", "out", "also", "more", "first", "get", "one",
}


def load_scoring_config() -> dict:
    """Load scoring weights from config.yaml."""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")
    with open(config_path) as f:
        config = yaml.safe_load(f)
    return config.get("scoring", {
        "weights": {
            "hackernews": {"divisor": 10},
            "reddit": {"divisor": 5},
            "github": {"divisor": 50},
            "youtube": {"default": 50},
            "twitter": {"divisor": 2},
            "app_stores": {"default": 30},
            "gmail": {"default": 70},  # newsletter mentions are strong signals
        },
        "cross_source_multiplier": 1.5,
        "newsletter_mention_bonus": 15,  # bonus points if mentioned in a newsletter
        "velocity": {
            "lookback_days": 7,
            "acceleration_threshold": 2.0,
            "fading_threshold": 0.5,
        },
    })


def _extract_keywords(text: str) -> set:
    """Extract meaningful keywords from text for matching."""
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    words = set(text.split()) - STOPWORDS
    return {w for w in words if len(w) > 2}


def _jaccard_similarity(set_a: set, set_b: set) -> float:
    """Compute Jaccard similarity between two keyword sets."""
    if not set_a or not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union)


def normalize_score(item: ContentItem, weights: dict) -> float:
    """Normalize a ContentItem's raw score to 0-100 based on source type."""
    raw = item.score or 0
    source_lower = item.source.lower()
    category = item.category

    # Determine which weight config to use
    if category == "reddit":
        divisor = weights.get("reddit", {}).get("divisor", 5)
        normalized = raw / divisor
    elif "hackernews" in source_lower or "hn" in source_lower:
        divisor = weights.get("hackernews", {}).get("divisor", 10)
        normalized = raw / divisor
    elif category == "youtube":
        normalized = weights.get("youtube", {}).get("default", 50)
    elif category == "twitter":
        divisor = weights.get("twitter", {}).get("divisor", 2)
        normalized = raw / divisor
    elif category == "app_stores":
        normalized = weights.get("app_stores", {}).get("default", 30)
    elif category == "gmail" or "newsletter" in source_lower:
        base = weights.get("gmail", {}).get("default", 70)
        # The Neuron has stronger curation — score higher than generic newsletters
        normalized = base * 1.2 if "neuron" in source_lower else base
    elif category == "api_endpoints":
        normalized = weights.get("api_endpoints", {}).get("default", 45)
    else:
        # GitHub trending or other webfetch sources
        if item.extra.get("stars_today"):
            divisor = weights.get("github", {}).get("divisor", 50)
            normalized = item.extra["stars_today"] / divisor
        else:
            normalized = raw / 10 if raw else 30

    return max(1, min(100, normalized))


def find_newsletter_mentions(items: List[ContentItem]) -> dict:
    """Extract topics mentioned in newsletter items and build a lookup.
    Returns {keyword_set_hash: [newsletter_sources]} for cross-referencing."""
    newsletter_items = [i for i in items if i.category == "gmail" or "newsletter" in i.source.lower()]
    mentions = {}
    for item in newsletter_items:
        # Use title + description for keyword extraction
        text = f"{item.title} {item.description or ''} {item.raw_text or ''}"
        keywords = _extract_keywords(text)
        mentions[frozenset(keywords)] = item.source
    return newsletter_items, mentions


def apply_cross_source_multiplier(
    items: List[ContentItem], config: dict
) -> List[ContentItem]:
    """Group items by topic similarity. Items in 2+ sources get score boost.
    Items also mentioned in newsletters get an additional bonus."""
    multiplier = config.get("cross_source_multiplier", 1.5)
    newsletter_bonus = config.get("newsletter_mention_bonus", 15)
    weights = config.get("weights", {})

    # Extract newsletter items for cross-referencing
    newsletter_items, newsletter_keywords = find_newsletter_mentions(items)

    # Build keyword sets for all items
    item_keywords = []
    for item in items:
        kw = _extract_keywords(f"{item.title} {item.description or ''}")
        item_keywords.append(kw)

    # Group by similarity
    groups = []  # list of (set of item indices, merged keywords)
    assigned = set()

    for i, kw_i in enumerate(item_keywords):
        if i in assigned:
            continue
        group = {i}
        merged_kw = set(kw_i)
        for j, kw_j in enumerate(item_keywords):
            if j <= i or j in assigned:
                continue
            if _jaccard_similarity(kw_i, kw_j) > 0.35:
                group.add(j)
                merged_kw |= kw_j
                assigned.add(j)
        assigned.add(i)
        groups.append((group, merged_kw))

    # Score each item
    for group_indices, group_keywords in groups:
        sources_in_group = {items[i].category for i in group_indices}
        source_count = len(sources_in_group)

        # Check newsletter mentions for this topic
        mentioned_in_newsletter = False
        newsletter_sources = []
        for nl_kw_set, nl_source in newsletter_keywords.items():
            if _jaccard_similarity(group_keywords, nl_kw_set) > 0.25:
                mentioned_in_newsletter = True
                newsletter_sources.append(nl_source)

        for idx in group_indices:
            item = items[idx]
            base_score = normalize_score(item, weights)

            # Tiered cross-source multiplier: 1.3x for 2 sources, full for 3+
            if source_count >= 3:
                base_score *= multiplier
            elif source_count == 2:
                base_score *= (1 + (multiplier - 1) * 0.6)  # e.g. 1.3x when multiplier=1.5

            # Newsletter mention bonus — tiered by newsletter quality
            # Premium newsletters (human-curated, high signal) get higher bonus
            if mentioned_in_newsletter:
                has_premium = any(
                    "neuron" in s.lower() for s in newsletter_sources
                )
                base_score += newsletter_bonus * (1.5 if has_premium else 1.0)
                item.extra["mentioned_in_newsletters"] = newsletter_sources

            item.extra["normalized_score"] = max(1, min(100, base_score))
            item.extra["cross_source_count"] = source_count

    return items


def compute_velocity(days: int = 7) -> List[dict]:
    """Compare today's topics against previous days across ALL sources.
    Returns velocity data for each topic."""
    cached_days = list_cached_days()
    if len(cached_days) < 1:
        return []

    today = get_target_date()

    # Load all items per day
    daily_topics = {}  # {day: {topic_keywords_frozen: {sources, titles, max_score}}}
    source_keys = ["reddit", "youtube", "twitter", "app_stores", "api_endpoints"]

    for day in cached_days[-(days + 1):]:
        daily_topics[day] = {}
        for sk in source_keys:
            items = get_cached(sk, day)
            if not items:
                continue
            for item in items:
                kw = frozenset(_extract_keywords(item.title))
                if len(kw) < 2:
                    continue
                if kw not in daily_topics[day]:
                    daily_topics[day][kw] = {
                        "sources": set(),
                        "titles": [],
                        "max_score": 0,
                    }
                daily_topics[day][kw]["sources"].add(item.category)
                daily_topics[day][kw]["titles"].append(item.title)
                daily_topics[day][kw]["max_score"] = max(
                    daily_topics[day][kw]["max_score"], item.score or 0
                )

    if today not in daily_topics:
        return []

    # Compute velocity for today's topics
    velocities = []
    previous_days = [d for d in cached_days if d < today]

    for kw_set, today_data in daily_topics[today].items():
        # Find this topic in previous days (fuzzy match)
        first_seen = today
        days_active = 1
        prev_source_counts = []
        prev_titles = set()
        prev_sources = set()
        prev_max_score = 0

        for prev_day in sorted(previous_days):
            if prev_day not in daily_topics:
                continue
            # Check if topic existed on this day
            for prev_kw, prev_data in daily_topics[prev_day].items():
                if _jaccard_similarity(kw_set, prev_kw) > 0.35:
                    if prev_day < first_seen:
                        first_seen = prev_day
                    days_active += 1
                    prev_source_counts.append(len(prev_data["sources"]))
                    prev_titles.update(prev_data["titles"])
                    prev_sources.update(prev_data["sources"])
                    prev_max_score = max(prev_max_score, prev_data["max_score"])
                    break

        today_count = len(today_data["sources"])

        # Determine velocity
        if days_active == 1:
            velocity = "new"
            emoji = "🆕"
        elif prev_source_counts:
            yesterday_count = prev_source_counts[-1]
            peak_count = max(prev_source_counts)
            if yesterday_count > 0 and today_count / yesterday_count >= 2.0:
                velocity = "accelerating"
                emoji = "🔥"
            elif peak_count > 0 and today_count / peak_count <= 0.5:
                velocity = "fading"
                emoji = "📉"
            else:
                velocity = "steady"
                emoji = "➡️"
        else:
            velocity = "new"
            emoji = "🆕"

        # Cross-day dedup: determine if this topic has genuinely new info
        # vs being the same news repeated across days.
        # "fresh" = first time seen
        # "deepened" = same topic but new sources, new titles, or score jumped 2x+
        # "repeat" = same story rehashed, no meaningful new info — skip in outputs
        if days_active == 1:
            freshness = "fresh"
        else:
            new_sources = set(today_data["sources"]) - prev_sources
            # Check if today's titles bring new keywords not in previous titles
            today_title_kw = set()
            for t in today_data["titles"]:
                today_title_kw |= _extract_keywords(t)
            prev_title_kw = set()
            for t in prev_titles:
                prev_title_kw |= _extract_keywords(t)
            new_keywords = today_title_kw - prev_title_kw
            score_jumped = (prev_max_score > 0 and
                           today_data["max_score"] / prev_max_score >= 2.0)

            if new_sources or len(new_keywords) >= 3 or score_jumped:
                freshness = "deepened"
            else:
                freshness = "repeat"

        velocities.append({
            "topic": today_data["titles"][0],  # representative title
            "keywords": list(kw_set)[:10],
            "velocity": velocity,
            "emoji": emoji,
            "first_seen": first_seen,
            "days_active": days_active,
            "source_count_today": today_count,
            "sources_today": list(today_data["sources"]),
            "max_score": today_data["max_score"],
            "freshness": freshness,
        })

    # Sort: fresh/deepened first, then by source count and score. Repeats sink to bottom.
    freshness_rank = {"fresh": 0, "deepened": 1, "repeat": 2}
    velocities.sort(key=lambda v: (freshness_rank.get(v.get("freshness", "fresh"), 0),
                                   -v["source_count_today"], -v["max_score"]))
    return velocities


def compute_weekly_aggregate(days: int = 7) -> dict:
    """Compute weekly aggregate for the /weekly skill."""
    cached_days = list_cached_days()
    if not cached_days:
        return {"persistent": [], "flash": [], "rising": [], "top_signals": []}

    # Track topic appearances across days
    topic_tracker = defaultdict(lambda: {
        "days": [], "sources_per_day": [], "max_score": 0, "titles": []
    })
    source_keys = ["reddit", "youtube", "twitter", "app_stores", "api_endpoints"]

    for day in cached_days[-days:]:
        for sk in source_keys:
            items = get_cached(sk, day)
            if not items:
                continue
            for item in items:
                kw = frozenset(_extract_keywords(item.title))
                if len(kw) < 2:
                    continue
                # Find matching topic or create new
                matched = False
                for existing_kw in list(topic_tracker.keys()):
                    if _jaccard_similarity(kw, existing_kw) > 0.35:
                        tracker = topic_tracker[existing_kw]
                        if day not in tracker["days"]:
                            tracker["days"].append(day)
                            tracker["sources_per_day"].append(1)
                        else:
                            tracker["sources_per_day"][-1] += 1
                        tracker["max_score"] = max(tracker["max_score"], item.score or 0)
                        tracker["titles"].append(item.title)
                        matched = True
                        break
                if not matched:
                    topic_tracker[kw] = {
                        "days": [day],
                        "sources_per_day": [1],
                        "max_score": item.score or 0,
                        "titles": [item.title],
                    }

    persistent = []
    flash = []
    rising = []

    for kw, data in topic_tracker.items():
        entry = {
            "topic": data["titles"][0],
            "days_active": len(data["days"]),
            "max_score": data["max_score"],
            "date_range": f"{data['days'][0]} to {data['days'][-1]}",
        }
        if len(data["days"]) >= 5:
            # Check trajectory
            counts = data["sources_per_day"]
            if len(counts) >= 3 and counts[-1] > counts[0]:
                entry["trajectory"] = "rising"
            elif len(counts) >= 3 and counts[-1] < counts[0]:
                entry["trajectory"] = "declining"
            else:
                entry["trajectory"] = "stable"
            persistent.append(entry)
        elif len(data["days"]) <= 2 and data["max_score"] > 50:
            flash.append(entry)
        elif len(data["days"]) >= 2:
            counts = data["sources_per_day"]
            if len(counts) >= 2 and counts[-1] > counts[0]:
                rising.append(entry)

    persistent.sort(key=lambda x: -x["days_active"])
    flash.sort(key=lambda x: -x["max_score"])
    rising.sort(key=lambda x: -x["max_score"])

    return {
        "persistent": persistent[:10],
        "flash": flash[:10],
        "rising": rising[:10],
        "top_signals": sorted(
            persistent + flash + rising,
            key=lambda x: -x["max_score"]
        )[:5],
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Signal Hunter — Scoring Engine")
    parser.add_argument("--weekly", action="store_true", help="Output weekly aggregate instead of daily velocity")
    parser.add_argument("--date", type=str, default=None, help="Target date (YYYY-MM-DD). Defaults to yesterday. Use 'today' for today.")
    args = parser.parse_args()

    if args.date:
        from src.cache import set_target_date
        set_target_date(args.date)

    if args.weekly:
        result = compute_weekly_aggregate()
    else:
        result = {
            "velocity": compute_velocity(),
            "date": get_target_date(),
        }

    json.dump(result, sys.stdout, indent=2, default=str)


if __name__ == "__main__":
    main()
