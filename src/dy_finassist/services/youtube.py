from __future__ import annotations

from typing import Optional

from googleapiclient.discovery import build

from ..config import get_settings


class YouTubeUnavailable(RuntimeError):
    """Raised when the YouTube API cannot be used."""


def search_video(query: str, *, max_results: int = 1) -> Optional[tuple[str, str]]:
    """Return the first matching YouTube video (title, url) or ``None``."""

    settings = get_settings()
    if not settings.youtube_api_key:
        raise YouTubeUnavailable("Missing YOUTUBE_API_KEY environment variable.")

    youtube = build("youtube", "v3", developerKey=settings.youtube_api_key)
    response = youtube.search().list(
        q=query,
        part="snippet",
        maxResults=max_results,
        type="video",
    ).execute()

    items = response.get("items", [])
    if not items:
        return None

    first = items[0]
    video_id = first["id"]["videoId"]
    title = first["snippet"]["title"]
    return title, f"https://www.youtube.com/watch?v={video_id}"


__all__ = ["search_video", "YouTubeUnavailable"]
