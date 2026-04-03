"""
yt_transcriber.py — YouTube Transcription Engine
=================================================
Three-tier caption strategy, no audio download required.

TIER 1 — youtube-transcript-api  (~1s)
    Fetches YouTube's own caption XML. Fast but can be blocked
    (502 / RequestBlocked) from server/Docker IPs without cookies.

TIER 2 — yt-dlp --write-subs  (~3-5s, still no audio download)
    Downloads only the .vtt subtitle file. Handles YouTube anti-bot
    much better. Works from Docker/server IPs.

TIER 3 — Report no captions available (no Whisper fallback)
    If both tiers fail the video genuinely has no captions.

Install:
    pip install youtube-transcript-api yt-dlp
"""

import os
import re
import html
import tempfile
from typing import Optional, Any, Dict


# ── Helpers ───────────────────────────────────────────────────────────────────

def extract_video_id(url: str) -> Optional[str]:
    """Extract 11-char video ID from any YouTube URL."""
    patterns = [
        r"(?:youtube\.com/watch\?[^#]*v=|youtu\.be/|youtube\.com/embed/|youtube\.com/shorts/)([a-zA-Z0-9_-]{11})",
        r"[?&]v=([a-zA-Z0-9_-]{11})",
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None


def _vtt_to_text(vtt: str) -> str:
    """
    Convert WebVTT string to clean plain text.
    Strips timestamps, HTML tags, cue numbers, and deduplicates
    the rolling lines that auto-captions repeat.
    """
    seen: set = set()
    parts = []
    for line in vtt.splitlines():
        line = line.strip()
        if (not line
                or line.startswith("WEBVTT")
                or "-->" in line
                or re.match(r"^\d+$", line)
                or line.startswith(("NOTE ", "Kind:", "Language:"))):
            continue
        # Strip inline tags: <c>, <b>, <i>, <00:00:00.000>
        clean = re.sub(r"<[^>]+>", "", line).strip()
        clean = html.unescape(clean)
        if clean and clean not in seen:
            seen.add(clean)
            parts.append(clean)
    return " ".join(parts)


# ── Tier 1: youtube-transcript-api (v1.x compatible) ─────────────────────────

def _fetch_via_transcript_api(video_id: str, languages: Optional[list] = None) -> Optional[str]:
    """
    Use youtube-transcript-api to fetch captions.
    Compatible with both v0.6.x and v1.x (breaking API change in v1.0).

    v1.x changes:
     - transcript.fetch() now returns FetchedTranscript (iterable of
       FetchedTranscriptSnippet with .text/.start/.duration attributes)
     - get_transcript / list_transcripts static methods removed
     - New exception: RequestBlocked (YouTube IP ban / 502)
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound
        try:
            from youtube_transcript_api import RequestBlocked
        except ImportError:
            RequestBlocked = None
        try:
            from youtube_transcript_api import TranscriptsDisabled
        except ImportError:
            TranscriptsDisabled = None
    except ImportError:
        return None

    preferred = languages or ["en", "en-US", "en-GB"]

    try:
        ytt = YouTubeTranscriptApi()
        transcript_list = ytt.list(video_id)

        transcript = None
        try:
            transcript = transcript_list.find_manually_created_transcript(preferred)
        except (NoTranscriptFound, Exception):
            pass

        if transcript is None:
            try:
                transcript = transcript_list.find_generated_transcript(preferred)
            except (NoTranscriptFound, Exception):
                available = list(transcript_list)
                transcript = available[0] if available else None

        if transcript is None:
            return None

        fetched = transcript.fetch()

        parts = []
        for snippet in fetched:
            # v1.x uses attribute access; v0.x used dict access
            if hasattr(snippet, "text"):
                text = snippet.text
            elif isinstance(snippet, dict):
                text = snippet.get("text", "")
            else:
                text = str(snippet)
            text = text.strip()
            if text and text not in ("[Music]", "[Applause]", "[Laughter]"):
                parts.append(text)

        return " ".join(parts) if parts else None

    except Exception as e:
        name = type(e).__name__
        # RequestBlocked = YouTube is rate-limiting/blocking this IP
        if RequestBlocked and isinstance(e, RequestBlocked):
            print(f"[yt_transcriber] Tier 1: RequestBlocked (IP blocked by YouTube) — trying tier 2")
        elif "502" in str(e) or "blocked" in str(e).lower():
            print(f"[yt_transcriber] Tier 1: {name} (likely IP block) — trying tier 2")
        else:
            print(f"[yt_transcriber] Tier 1: {name}: {e} — trying tier 2")
        return None


# ── Tier 2: yt-dlp subtitle extraction (no audio) ────────────────────────────

def _fetch_via_ytdlp_subs(url: str, languages: Optional[list] = None) -> Optional[str]:
    """
    Download ONLY the .vtt subtitle file using yt-dlp (no audio).
    yt-dlp uses a real browser-like client and handles IP/cookie issues
    much better than the transcript API.
    """
    try:
        import yt_dlp
    except ImportError:
        print("[yt_transcriber] Tier 2: yt-dlp not installed")
        return None

    sub_langs = (languages or ["en", "en-US", "en-GB"])

    with tempfile.TemporaryDirectory() as tmpdir:
        ydl_opts = {
            "skip_download": True,           # ← no audio, no video
            "writesubtitles": True,          # manual captions
            "writeautomaticsub": True,       # auto-generated captions
            "subtitleslangs": sub_langs,
            "subtitlesformat": "vtt",
            "outtmpl": os.path.join(tmpdir, "%(id)s.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            # Find any .vtt file written to tmpdir
            vtt_path = None
            for fname in os.listdir(tmpdir):
                if fname.endswith(".vtt"):
                    vtt_path = os.path.join(tmpdir, fname)
                    break

            if vtt_path is None:
                return None

            with open(vtt_path, "r", encoding="utf-8", errors="replace") as f:
                raw = f.read()

            text = _vtt_to_text(raw)
            return text.strip() if text.strip() else None

        except Exception as e:
            print(f"[yt_transcriber] Tier 2 error: {type(e).__name__}: {e}")
            return None


# ── Metadata ──────────────────────────────────────────────────────────────────

def _get_metadata(url: str) -> dict:
    """Get title/duration/id without downloading anything."""
    try:
        import yt_dlp
        opts = {"quiet": True, "no_warnings": True, "skip_download": True}
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                "title": info.get("title", ""),
                "duration": float(info.get("duration") or 0),
                "video_id": info.get("id", ""),
            }
    except Exception:
        return {"title": "", "duration": 0.0, "video_id": extract_video_id(url) or ""}


# ── Public API ────────────────────────────────────────────────────────────────

def transcribe_url(
    url: str,
    languages: Optional[list] = None,
    model_size: str = "base",   # kept for backwards compat, ignored
    force_whisper: bool = False, # kept for backwards compat, ignored
) -> dict:
    """
    Fetch a transcript for a YouTube video.

    Returns
    -------
    dict with keys:
        title       str
        url         str
        video_id    str
        transcript  str    (empty on failure)
        duration    float  (seconds, 0 if unknown)
        source      str    "captions_api" | "ytdlp_subs" | "none"
        error       str | None
    """
    meta = _get_metadata(url)
    video_id = meta["video_id"] or extract_video_id(url) or ""
    label = meta.get("title") or video_id or url[:60]

    base = {
        "title": meta["title"],
        "url": url,
        "video_id": video_id,
        "duration": meta["duration"],
        "transcript": "",
        "source": "none",
        "error": None,
    }

    # Tier 1 — transcript API
    if video_id:
        text = _fetch_via_transcript_api(video_id, languages)
        if text:
            try:
                print(f"[yt_transcriber] ✓ tier1 '{label}' — {len(text):,} chars")
            except Exception:
                # Fallback if console encoding doesn't handle checkmark
                print(f"[yt_transcriber] [tier1] '{label}' — {len(text):,} chars")
            return {**base, "transcript": text, "source": "captions_api"}

    # Tier 2 — yt-dlp subs
    text = _fetch_via_ytdlp_subs(url, languages)
    if text:
        try:
            print(f"[yt_transcriber] ✓ tier2 '{label}' — {len(text):,} chars")
        except Exception:
            print(f"[yt_transcriber] [tier2] '{label}' — {len(text):,} chars")
        return {**base, "transcript": text, "source": "ytdlp_subs"}

    msg = "No captions found (both tiers failed — video may have no subtitles)"
    print(f"[yt_transcriber] ✗ '{label}'")
    return {**base, "error": msg}


def get_video_chain(url: str, n: int = 5) -> list:
    """
    Return up to n {"url", "title"} dicts from a playlist, channel, or
    single video URL.
    """
    try:
        import yt_dlp
    except ImportError:
        return [{"url": url, "title": ""}]

    opts = {"quiet": True, "no_warnings": True,
            "extract_flat": True, "skip_download": True}
    videos: list = []
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info.get("_type") == "playlist":
                for entry in (info.get("entries") or []):
                    if not entry:
                        continue
                    eurl = entry.get("url") or entry.get("webpage_url", "")
                    if eurl and not eurl.startswith("http"):
                        eurl = f"https://www.youtube.com/watch?v={eurl}"
                    if eurl:
                        videos.append({"url": eurl, "title": entry.get("title", "")})
                    if len(videos) >= n:
                        break
            else:
                videos.append({"url": url, "title": info.get("title", "")})
    except Exception as e:
        print(f"[yt_transcriber] get_video_chain: {e}")

    return (videos or [{"url": url, "title": ""}])[:n]


def transcribe_chain(
    url: str,
    n: int = 5,
    languages: Optional[list] = None,
    model_size: str = "base",  # backwards compat, ignored
) -> list:
    """Transcribe n videos starting from url. Returns list of transcribe_url() dicts."""
    chain = get_video_chain(url, n)
    results = []
    for i, v in enumerate(chain, 1):
        print(f"[yt_transcriber] [{i}/{len(chain)}] {v.get('title') or v['url'][:70]}")
        results.append(transcribe_url(v["url"], languages=languages))
    ok = sum(1 for r in results if r.get("transcript"))
    print(f"[yt_transcriber] Done — {ok}/{len(results)} transcribed")
    return results


def create_yt_transcriber():
    """Factory matching original interface."""
    return {
        "transcribe_url": transcribe_url,
        "get_video_chain": get_video_chain,
        "transcribe_chain": transcribe_chain,
    }


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python yt_transcriber.py <url> [n]")
        sys.exit(1)

    url = sys.argv[1]
    n   = int(sys.argv[2]) if len(sys.argv) > 2 else 1

    if n == 1:
        r = transcribe_url(url)
        print(f"\nTitle:  {r['title']}")
        print(f"Source: {r['source']}")
        print(f"Length: {len(r['transcript']):,} chars")
        if r["error"]:
            print(f"Error:  {r['error']}")
        else:
            print(f"\n--- TRANSCRIPT (first 2000 chars) ---")
            print(r["transcript"][:2000])
            if len(r["transcript"]) > 2000:
                print(f"\n[... +{len(r['transcript'])-2000:,} more chars]")
    else:
        results = transcribe_chain(url, n=n)
        print("\n=== Summary ===")
        for r in results:
            ok = "✓" if r.get("transcript") else "✗"
            print(f"  {ok} [{r['source']:14}] {r.get('title') or r['url'][:60]}")