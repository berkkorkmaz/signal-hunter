from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ContentItem(BaseModel):
    source: str  # "hackernews", "reddit", "youtube", etc.
    category: str  # "webfetch", "reddit", "youtube", "twitter", etc.
    title: str
    url: Optional[str] = None
    description: Optional[str] = None
    score: Optional[int] = None  # upvotes, stars, likes
    author: Optional[str] = None
    timestamp: Optional[datetime] = None
    tags: List[str] = []
    raw_text: Optional[str] = None  # full text for newsletters/transcripts
    extra: dict = {}  # source-specific metadata
