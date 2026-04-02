"""
yt_transcriber.py — YouTube Transcription Engine
=================================================
Downloads audio from YouTube videos using yt-dlp,
transcribes speech to text using Whisper,
and follows video chains for sequential learning.

Usage: /yt <n> <url> — loads n videos starting from url,
       transcribes each, and teaches the brain.

Dependencies:
    pip install yt-dlp openai-whisper
    Also requires ffmpeg on PATH.
"""

import os
import re
import json
import tempfile
import time
from typing import Optional, Generator

# ── Lazy-loaded model (only load whisper when first needed) ──────────────
_whisper_model = None
_whisper_model_size = "base"  # tiny/base/small/medium/large


def _get_whisper_model(model_size: str = None):
    """Lazy-load the Whisper model (expensive, do once)."""
    global _whisper_model, _whisper_model_size
    size = model_size or _whisper_model_size
    if _whisper_model is None or _whisper_model_size != size:
        import whisper
        _whisper_model = whisper.load_model(size)
        _whisper_model_size = size
    return _whisper_model


def transcribe_url(url: str, model_size: str = "base") -> dict:
    """
    Download audio from a YouTube URL and transcribe it.

    Returns
    -------
    dict with keys:
        title (str): video title
        url (str): the YouTube URL
        transcript (str): full transcript text
        duration (float): video duration in seconds
        error (str): error message if any, None on success
    """
    import yt_dlp

    result = {
        "title": "",
        "url": url,
        "transcript": "",
        "duration": 0.0,
        "error": None,
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        audio_path = os.path.join(tmpdir, "audio.%(ext)s")

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": audio_path,
            "quiet": True,
            "no_warnings": True,
            "extract_audio": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                result["title"] = info.get("title", "")
                result["duration"] = info.get("duration", 0.0)

                # Find the downloaded audio file
                downloaded = ydl.prepare_filename(info)
                # yt-dlp may change the extension
                if not os.path.exists(downloaded):
                    # Try common audio extensions
                    for ext in [".m4a", ".webm", ".mp3", ".opus", ".wav"]:
                        candidate = os.path.join(tmpdir, f"audio{ext}")
                        if os.path.exists(candidate):
                            downloaded = candidate
                            break
                    else:
                        # Fallback: find any file in tmpdir
                        files = os.listdir(tmpdir)
                        if files:
                            downloaded = os.path.join(tmpdir, files[0])

                if not os.path.exists(downloaded):
                    result["error"] = "Audio file not found after download"
                    return result

                # Transcribe with Whisper
                model = _get_whisper_model(model_size)
                whisper_result = model.transcribe(downloaded)
                result["transcript"] = whisper_result.get("text", "").strip()

        except Exception as e:
            result["error"] = str(e)

    return result


def get_related_videos(url: str, n: int = 5) -> list:
    """
    Get related/next videos from a YouTube URL.

    Returns list of dicts with 'url' and 'title'.
    """
    import yt_dlp

    related = []
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "skip_download": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            # Check if it's a playlist
            if info.get("_type") == "playlist":
                for entry in info.get("entries", []):
                    if entry and entry.get("url"):
                        related.append({
                            "url": entry["url"],
                            "title": entry.get("title", "Unknown"),
                        })
                    if len(related) >= n:
                        break

            # Also check related videos
            if len(related) < n and "related_videos" in info:
                for rv in info["related_videos"]:
                    if rv.get("url"):
                        related.append({
                            "url": rv["url"],
                            "title": rv.get("title", "Unknown"),
                        })
                    if len(related) >= n:
                        break

    except Exception:
        pass

    # If no related videos found, just return the original URL
    if not related:
        related = [{"url": url, "title": "Original video"}]

    return related[:n]


def get_playlist_videos(url: str, n: int = 5) -> list:
    """
    Extract videos from a YouTube playlist URL.

    Returns list of dicts with 'url' and 'title'.
    """
    import yt_dlp

    videos = []
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "skip_download": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info.get("_type") == "playlist":
                for entry in info.get("entries", []):
                    if entry and entry.get("url"):
                        videos.append({
                            "url": entry["url"],
                            "title": entry.get("title", "Unknown"),
                        })
                    if len(videos) >= n:
                        break
    except Exception:
        pass

    # If not a playlist, return just the single video
    if not videos:
        videos = [{"url": url, "title": "Single video"}]

    return videos[:n]


def get_video_chain(url: str, n: int = 5) -> list:
    """
    Get a chain of n videos starting from the given URL.
    Handles playlists, related videos, or single videos.
    """
    # First try as playlist
    videos = get_playlist_videos(url, n)
    if len(videos) > 1:
        return videos

    # Fall back to related videos
    videos = get_related_videos(url, n)
    return videos


def create_yt_transcriber():
    """Factory function."""
    return {
        "transcribe_url": transcribe_url,
        "get_video_chain": get_video_chain,
    }
