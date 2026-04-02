"""
yt_transcriber.py — YouTube Transcription Engine
=================================================
Fetches transcripts from YouTube videos.

FAST PATH  (~1s/video):  youtube-transcript-api fetches YouTube's own
                         auto-generated or manual captions directly.
                         No audio download. No ffmpeg. No Whisper.

Usage:
    pip install youtube-transcript-api yt-dlp

/yt <n> <url> — loads n videos starting from url,
                transcribes each, and teaches the brain.
"""

import os
import re
import json
import tempfile
import time
from typing import Optional

# ── Video ID extraction ───────────────────────────────────────────────────────

def extract_video_id(url: str) -> Optional[str]:
    """
    Extract YouTube video ID from any YouTube URL format.

    Handles:
        https://www.youtube.com/watch?v=VIDEO_ID
        https://youtu.be/VIDEO_ID
        https://www.youtube.com/embed/VIDEO_ID
        https://www.youtube.com/shorts/VIDEO_ID
    """
    patterns = [
        r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/shorts/)([a-zA-Z0-9_-]{11})",
        r"[?&]v=([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


# ── Fast path: YouTube native captions ────────────────────────────────────────

def _fetch_captions(video_id: str, languages: Optional[list] = None) -> Optional[str]:
    """
    Fetch YouTube's own captions via youtube-transcript-api.
    Returns plain text or None if no captions available.

    Preference order:
        1. Manual English captions (highest quality)
        2. Auto-generated English captions (very common)
        3. Any other manual captions
        4. Any other auto-generated captions
    """
    try:
        import importlib
        yttapi_mod = importlib.import_module("youtube_transcript_api")
        YouTubeTranscriptApi = yttapi_mod.YouTubeTranscriptApi
        NoTranscriptFound = yttapi_mod.NoTranscriptFound
        TranscriptsDisabled = getattr(yttapi_mod, "TranscriptsDisabled", Exception)
    except ImportError:
        return None  # library not installed — caller will use slow path

    try:
        ytt = YouTubeTranscriptApi()
        transcript_list = ytt.list(video_id)

        # Try preferred languages first (manual > auto-generated)
        preferred = languages or ["en", "en-US", "en-GB"]

        try:
            transcript = transcript_list.find_manually_created_transcript(preferred)
        except NoTranscriptFound:
            try:
                transcript = transcript_list.find_generated_transcript(preferred)
            except NoTranscriptFound:
                # Fall back to whatever is available
                available = list(transcript_list)
                if not available:
                    return None
                transcript = available[0]

        entries = transcript.fetch()
        # Join all text segments into a clean paragraph
        text = " ".join(
            entry.text.strip()
            for entry in entries
            if entry.text.strip() and entry.text.strip() != "[Music]"
        )
        return text if text else None

    except Exception:
        return None


def _fetch_captions_with_timestamps(video_id: str, languages: Optional[list] = None) -> Optional[list]:
    """
    Same as _fetch_captions but returns list of {start, text} dicts.
    Useful for chapter-aware segmentation.
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound
        ytt = YouTubeTranscriptApi()
        transcript_list = ytt.list(video_id)
        preferred = languages or ["en", "en-US", "en-GB"]
        try:
            transcript = transcript_list.find_manually_created_transcript(preferred)
        except NoTranscriptFound:
            transcript = transcript_list.find_generated_transcript(preferred)
        return [{"start": e.start, "text": e.text} for e in transcript.fetch()]
    except Exception:
        return None


# Note: This module now uses a caption-first strategy (youtube-transcript-api).
# We intentionally removed any Whisper fallback: if captions are not available
# the transcriber will report that no transcript exists.


# ── Public API ────────────────────────────────────────────────────────────────

def transcribe_url(
    url: str,
    model_size: str = "base",
    languages: Optional[list[str]] = None,
    force_whisper: bool = False,
) -> dict:
    """
    Get a transcript for a YouTube video.

    Strategy:
      1. Try YouTube's native captions (fast, ~1 second, no dependencies)
      2. Fall back to Whisper if no captions exist (slow, requires ffmpeg)

    Parameters
    ----------
    url : str
        YouTube video URL (any format)
    model_size : str
        Whisper model size used only if captions unavailable.
        Options: "tiny" (fastest), "base", "small", "medium", "large"
    languages : list[str], optional
        Preferred caption languages in order. Default: ["en", "en-US", "en-GB"]
    force_whisper : bool
        Skip caption check and always use Whisper (for testing/comparison).

    Returns
    -------
    dict
        {
            title       (str):   video title
            url         (str):   the input URL
            video_id    (str):   YouTube video ID
            transcript  (str):   full transcript text
            duration    (float): video duration in seconds (0 if unknown)
            source      (str):   "captions" | "whisper" | "error"
            language    (str):   detected/used language
            error       (str):   error message or None
        }
    """
    # Get video metadata (title, duration) via yt-dlp — lightweight, no download
    title = ""
    duration = 0.0
    video_id = extract_video_id(url)

    try:
        import yt_dlp
        ydl_opts = {"quiet": True, "no_warnings": True, "skip_download": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore
            info = ydl.extract_info(url, download=False)
            title = info.get("title", "")
            duration = float(info.get("duration") or 0)
            if not video_id:
                video_id = info.get("id", "")
    except Exception:
        pass  # metadata is nice-to-have, not required

    base = {"title": title, "url": url, "video_id": video_id or "",
            "duration": duration, "language": "en", "error": None}

    # Fast path first
    if video_id:
        transcript = _fetch_captions(video_id, languages)
        if transcript:
            print(f"[yt_transcriber] ✓ Captions fetched for '{title or video_id}' ({len(transcript)} chars)")
            return {**base, "transcript": transcript, "source": "captions"}

    # No captions available — report absence (no Whisper fallback)
    msg = "No captions available for this video"
    print(f"[yt_transcriber] ✗ {msg} for '{title or video_id}'")
    return {**base, "transcript": "", "source": "none", "error": msg}


def get_video_chain(url: str, n: int = 5) -> list:
    """
    Get a chain of n videos starting from the given URL.
    Handles playlists, channels, or single videos.

    Returns list of {"url": ..., "title": ...} dicts.
    """
    try:
        import yt_dlp
    except ImportError:
        return [{"url": url, "title": ""}]

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "skip_download": True,
    }

    videos = []
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore
            info = ydl.extract_info(url, download=False)

            if info.get("_type") == "playlist":
                for entry in (info.get("entries") or []):
                    if entry and entry.get("url"):
                        entry_url = entry["url"]
                        # Playlist entries may give just the video ID
                        if not entry_url.startswith("http"):
                            entry_url = f"https://www.youtube.com/watch?v={entry_url}"
                        videos.append({"url": entry_url, "title": entry.get("title", "")})
                    if len(videos) >= n:
                        break
            else:
                # Single video: include it and any listed related videos
                videos.append({"url": url, "title": info.get("title", "")})
                for rv in (info.get("related_videos") or []):
                    if rv.get("url") and len(videos) < n:
                        videos.append({"url": rv["url"], "title": rv.get("title", "")})
    except Exception:
        pass

    if not videos:
        videos = [{"url": url, "title": ""}]

    return videos[:n]


def transcribe_chain(
    url: str,
    n: int = 5,
    model_size: str = "base",
    languages: Optional[list] = None,
) -> list:
    """
    Transcribe n videos starting from the given URL.

    Returns list of transcribe_url() result dicts.
    Prints progress as it goes.
    """
    chain = get_video_chain(url, n)
    results = []

    for i, video in enumerate(chain, 1):
        print(f"[yt_transcriber] [{i}/{len(chain)}] {video.get('title') or video['url']}")
        result = transcribe_url(
            video["url"],
            model_size=model_size,
            languages=languages,
        )
        if result.get("error"):
            print(f"  ✗ Error: {result['error']}")
        else:
            src = result.get("source", "?")
            chars = len(result.get("transcript", ""))
            print(f"  ✓ {src} — {chars:,} characters")
        results.append(result)

    return results


def create_yt_transcriber():
    """Factory function matching original interface."""
    return {
        "transcribe_url": transcribe_url,
        "get_video_chain": get_video_chain,
        "transcribe_chain": transcribe_chain,
    }


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python yt_transcriber.py <url> [n] [model_size]")
        print("  url        : YouTube video or playlist URL")
        print("  n          : number of videos to process (default: 1)")
        print("  model_size : whisper model if needed (default: base)")
        sys.exit(1)

    url = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    size = sys.argv[3] if len(sys.argv) > 3 else "base"

    if n == 1:
        result = transcribe_url(url, model_size=size)
        print(f"\nTitle:    {result['title']}")
        print(f"Source:   {result['source']}")
        print(f"Duration: {result['duration']:.0f}s")
        print(f"Length:   {len(result['transcript'])} chars")
        print(f"\n--- TRANSCRIPT ---\n{result['transcript'][:2000]}")
        if len(result['transcript']) > 2000:
            print(f"\n[... {len(result['transcript']) - 2000} more chars ...]")
    else:
        results = transcribe_chain(url, n=n, model_size=size)
        print(f"\n=== Summary: {len(results)} videos ===")
        for r in results:
            status = "✓" if not r.get("error") else "✗"
            print(f"  {status} [{r.get('source','?')}] {r.get('title') or r['url'][:60]}")