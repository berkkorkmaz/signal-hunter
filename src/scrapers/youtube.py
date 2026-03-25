import json
import subprocess
import sys
import os
from datetime import datetime, timezone, timedelta
from typing import List, Optional
import feedparser
from youtube_transcript_api import YouTubeTranscriptApi
from src.scrapers.base import BaseScraper
from src.models.content import ContentItem

YTDLP = os.path.join(os.path.dirname(sys.executable), "yt-dlp")


class YouTubeScraper(BaseScraper):
    name = "youtube"
    category = "youtube"

    def __init__(self, channels: List[dict], hours: int = 48, fetch_transcripts: bool = True):
        self.channels = channels
        self.cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=hours)
        self.fetch_transcripts = fetch_transcripts

    def fetch(self) -> List[ContentItem]:
        items = []
        for ch in self.channels:
            channel_id = ch.get("channel_id")
            channel_name = ch.get("channel", ch.get("name", "unknown"))
            if not channel_id:
                channel_id = self._resolve_channel_id_ytdlp(channel_name)
                if not channel_id:
                    print(f"[WARN] youtube: could not resolve channel ID for {channel_name}", file=sys.stderr)
                    continue
            channel_items = self._fetch_channel(channel_id, channel_name)
            # Fetch transcripts for new videos
            if self.fetch_transcripts:
                for item in channel_items:
                    vid = item.extra.get("video_id")
                    if vid:
                        transcript = self._fetch_transcript(vid)
                        if transcript:
                            item.raw_text = transcript
                            item.extra["has_transcript"] = True
            items.extend(channel_items)
        return items

    def _resolve_channel_id_ytdlp(self, handle: str) -> Optional[str]:
        """Resolve a YouTube handle to channel ID using yt-dlp."""
        clean = handle.lstrip("@")
        try:
            result = subprocess.run(
                [YTDLP, "--flat-playlist", "--playlist-end", "1", "-j",
                 f"https://www.youtube.com/@{clean}/videos"],
                capture_output=True, text=True, timeout=30,
            )
            if result.stdout.strip():
                data = json.loads(result.stdout.strip().split("\n")[0])
                return data.get("playlist_channel_id")
        except Exception:
            pass
        return None

    def _fetch_channel(self, channel_id: str, channel_name: str) -> List[ContentItem]:
        feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        feed = feedparser.parse(feed_url)
        items = []
        for entry in feed.entries:
            published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            if published < self.cutoff:
                continue
            video_id = entry.yt_videoid if hasattr(entry, "yt_videoid") else entry.link.split("v=")[-1]
            items.append(ContentItem(
                source=channel_name,
                category="youtube",
                title=entry.title,
                url=f"https://www.youtube.com/watch?v={video_id}",
                description=entry.get("summary", "")[:500] if entry.get("summary") else None,
                author=entry.get("author", channel_name),
                timestamp=published,
                extra={
                    "channel_id": channel_id,
                    "video_id": video_id,
                },
            ))
        return items

    def _fetch_transcript(self, video_id: str) -> Optional[str]:
        """Fetch transcript using youtube-transcript-api."""
        try:
            api = YouTubeTranscriptApi()
            transcript = api.fetch(video_id)
            text = " ".join([snippet.text for snippet in transcript.snippets])
            return text
        except Exception as e:
            print(f"[WARN] youtube: transcript failed for {video_id}: {e}", file=sys.stderr)
            return None
