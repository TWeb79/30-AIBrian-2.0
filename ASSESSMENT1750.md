# BRAIN 2.0 — Action List
**Date:** 2026-04-04  
**Based on:** Full codebase audit (statusanalysis.md + live code trace)

---

## All Actions Completed

| # | Item | Status |
|---|------|--------|
| 1 | BUG-1: `_status()` uses total_steps | ✅ Done |
| 2 | BUG-2: BrainStore env var alignment | ✅ Done |
| 3 | BUG-3: LLM gate respects vocabulary | ✅ Done |
| 4 | BUG-4: Auto-train vocabulary on cold start | ✅ Done |
| 5 | BUG-5: Remove vocabulary persist throttle | ✅ Done |
| 6 | ACTION-1: Sentence templates in PhonBuf | ✅ Done |
| 7 | ACTION-2: Wire ACh to thinking_steps | ✅ Done |
| 8 | ACTION-3: Richer memory context | ✅ Done |
| 9 | ACTION-4: Proactive messages via WebSocket | ✅ Done |
| 10 | ACTION-5: Self-initiated idle thoughts | ✅ Done |
| 11 | ACTION-6: Better proactive prompt | ✅ Done |
| 12 | ACTION-7: EIBalancedRegion crash fix | ✅ Done |
| 13 | ACTION-8: Competitive decay cap | ✅ Done |
| 14 | ACTION-9: STDP LTP/LTD event counters | ✅ Done |
| 15 | ACTION-10: `/api/brain/health` endpoint | ✅ Done |
| 16 | ACTION-11: Full neuromodulator populations | ✅ Done |
| 17 | ACTION-12: E/I balance PV/SST (documented) | ✅ Done |
| 18 | ACTION-13: AttractorChainer transition tests | ✅ Done |
| 19 | ACTION-14: PredictiveHierarchy observability | ✅ Done |

---

## Persistence Verification Checklist

Run this to confirm state is actually surviving reboots:

```bash
# 1. Start brain fresh, send a few messages
curl -s http://localhost:8030/api/vocabulary | jq .vocabulary_size

# 2. Restart the container
docker-compose restart brain-api
sleep 10

# 3. Check vocabulary survived
curl -s http://localhost:8030/api/vocabulary | jq .vocabulary_size

# 4. Verify brain_state directory exists on host
ls -la brain_state/vocabulary/

# 5. Check env var alignment
docker exec brain-api env | grep -E "BRAIN_STATE|PERSIST_DIR"
```
