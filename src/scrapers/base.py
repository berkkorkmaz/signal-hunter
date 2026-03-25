import sys
from abc import ABC, abstractmethod
from typing import List
from src.models.content import ContentItem


class BaseScraper(ABC):
    """Base class for all scrapers. Each scraper must implement fetch()."""

    name: str = "base"
    category: str = "unknown"

    @abstractmethod
    def fetch(self) -> List[ContentItem]:
        """Fetch content items from the source. Must be implemented by subclasses."""
        ...

    def safe_fetch(self) -> List[ContentItem]:
        """Wrapper that catches all exceptions and returns partial results."""
        try:
            items = self.fetch()
            print(f"[OK] {self.name}: {len(items)} items", file=sys.stderr)
            return items
        except Exception as e:
            print(f"[WARN] {self.name} failed: {e}", file=sys.stderr)
            return []
