# External routes - /api/yt, /api/grep, /api/wiki
import asyncio
import os
import re
import json
import time
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from fastapi import APIRouter, HTTPException
from api.config import brain
from api.models import YTRequest, GrepRequest

router = APIRouter()

def _slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9_-]", "_", s.strip().lower())


@router.post("/yt")
async def yt_transcribe(req: YTRequest):
    """YouTube transcription endpoint."""
    from yt_transcriber import transcribe_url, get_video_chain

    url = req.url
    n = min(max(req.n, 1), 10)

    if not url:
        raise HTTPException(status_code=400, detail="No URL provided")

    loop = asyncio.get_event_loop()

    try:
        videos = await loop.run_in_executor(None, get_video_chain, url, n)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get video chain: {e}")

    async def _process_single_video(video: dict) -> dict:
        video_url = video["url"]
        video_title = video.get("title", "Unknown")
        try:
            try:
                from yt_transcriber import _fetch_via_transcript_api, extract_video_id
            except Exception:
                _fetch_via_transcript_api = None
                extract_video_id = None

            result = None
            if _fetch_via_transcript_api and extract_video_id:
                vid = extract_video_id(video_url)
                if vid:
                    text = await loop.run_in_executor(None, _fetch_via_transcript_api, vid, ['de','en'])
                    if text:
                        result = {"title": video_title or vid, "url": video_url, "video_id": vid, "duration": 0, "transcript": text, "source": "captions_api", "error": None}

            if result is None:
                result = await loop.run_in_executor(None, transcribe_url, video_url, ['de','en'])

            if result.get("error"):
                return {"title": video_title, "url": video_url, "error": result["error"], "transcript_length": 0, "words_learned": 0}

            transcript = result.get("transcript", "")
            chunk_size = 200
            words = transcript.split()
            words_learned = 0
            for i in range(0, len(words), chunk_size):
                chunk = " ".join(words[i:i+chunk_size])
                await asyncio.to_thread(brain.process_input_v01, chunk)
            words_learned = brain.phon_buffer.get_vocabulary_size()
            await asyncio.to_thread(brain.persist)

            try:
                with brain._lock:
                    brain.chat_history.append({"role": "assistant", "content": f"[transcript] {video_title}\n{transcript[:2000]}"})
            except Exception:
                pass

            return {"title": video_title, "url": video_url, "duration": result.get("duration", 0), "transcript_length": len(transcript), "words_learned": words_learned}
        except Exception as e:
            return {"title": video_title, "url": video_url, "error": str(e), "transcript_length": 0, "words_learned": 0}

    sem = asyncio.Semaphore(4)
    async def _bounded_process(v):
        async with sem:
            return await _process_single_video(v)

    tasks = [asyncio.create_task(_bounded_process(v)) for v in videos]
    results = await asyncio.gather(*tasks)

    await asyncio.to_thread(brain.persist)

    return {
        "videos_processed": len(results),
        "results": results,
        "vocabulary_size": brain.phon_buffer.get_vocabulary_size(),
    }


@router.post("/grep")
async def grep(req: GrepRequest):
    """Web crawling endpoint."""
    n = req.n
    start_url = req.url
    
    if n < 1 or n > 20:
        raise HTTPException(status_code=400, detail="n must be between 1 and 20")
    
    visited = set()
    results = []
    queue = [start_url]
    base_domain = urlparse(start_url).netloc
    
    while queue and len(results) < n:
        url = queue.pop(0)
        if url in visited:
            continue
        visited.add(url)
        
        try:
            response = await asyncio.to_thread(
                requests.get,
                url,
                timeout=10,
                headers={"User-Agent": "BRAIN20/0.1"},
            )
            status = response.status_code
            
            if response.ok:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                for script in soup(["script", "style"]):
                    script.decompose()
                
                content = soup.get_text(separator=' ', strip=True)
                content = ' '.join(content.split())
                
                for link in soup.find_all('a'):
                    href = link.get('href')
                    if href:
                        full_url = urljoin(url, href)
                        parsed = urlparse(full_url)
                        if (
                            parsed.netloc == base_domain
                            and full_url not in visited
                            and full_url not in queue
                            and len(queue) < 20
                        ):
                            queue.append(full_url)
            else:
                content = f"HTTP Error: {status}"
                
            results.append({
                "url": url,
                "status": status,
                "content": content[:5000]
            })
        except Exception as e:
            results.append({
                "url": url,
                "status": 0,
                "error": str(e)
            })
    
    return {
        "requested": n,
        "crawled": len(results),
        "start_url": start_url,
        "results": results
    }


def fetch_wikipedia_sync(topic: str, max_checked: int = 200000, timeout_seconds: int = 20) -> dict:
    """Search Wikipedia snapshot for a title match."""
    cache_dir = os.path.join("data", "wiki_cache")
    os.makedirs(cache_dir, exist_ok=True)
    slug = _slugify(topic)
    cache_path = os.path.join(cache_dir, f"{slug}.json")
    try:
        if os.path.exists(cache_path):
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass

    try:
        from datasets import load_dataset
    except Exception as e:
        return {"found": False, "error": f"datasets not available: {e}"}

    topic_norm = topic.strip().lower()
    best_candidate = None
    start = time.time()
    try:
        ds = load_dataset("wikipedia", "20220301.en", split="train", streaming=True)
        for i, rec in enumerate(ds):
            if time.time() - start > timeout_seconds:
                break
            if i >= max_checked:
                break

            title = rec.get("title") or ""
            text = rec.get("text") or rec.get("content") or ""
            if not title:
                continue

            tnorm = title.strip().lower()
            if tnorm == topic_norm:
                result = {"found": True, "title": title, "text": text}
                try:
                    with open(cache_path, "w", encoding="utf-8") as f:
                        json.dump(result, f, ensure_ascii=False)
                except Exception:
                    pass
                return result

            if topic_norm in tnorm or topic_norm in (text or "").lower():
                if not best_candidate:
                    best_candidate = {"found": True, "title": title, "text": text}

    except Exception as e:
        return {"found": False, "error": str(e)}

    if best_candidate:
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(best_candidate, f, ensure_ascii=False)
        except Exception:
            pass
        return best_candidate

    return {"found": False, "title": None, "text": ""}


@router.get("/wiki")
async def wiki(topic: str | None = None, persist: bool = False, max_chars: int = 50000):
    """Return Wikipedia article text."""
    if not topic:
        raise HTTPException(status_code=400, detail="topic query parameter is required")

    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(None, fetch_wikipedia_sync, topic)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not result.get("found"):
        return {"found": False, "message": "No article found", "error": result.get("error")}

    text = result.get("text") or ""
    if max_chars and len(text) > max_chars:
        text = text[:max_chars] + "\n\n[TRUNCATED]"

    out = {"found": True, "title": result.get("title"), "text": text, "source": "wikipedia_snapshot"}

    if persist:
        slug = _slugify(topic)
        cache_dir = os.path.join("data", "wiki_cache")
        os.makedirs(cache_dir, exist_ok=True)
        cache_path = os.path.join(cache_dir, f"{slug}.json")
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False)
        except Exception as e:
            print(f"[API /wiki] Failed to persist cache: {e}")

    return out