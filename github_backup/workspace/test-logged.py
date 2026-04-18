#!/usr/bin/env python3
"""加插樁 Log 的 search_and_detail"""
import sys, os, time, io

sys.path.insert(0, os.path.expanduser("~/.openclaw/skills/where-to-go/scripts"))
os.environ["PYTHONUNBUFFERED"] = "1"
os.chdir(os.path.expanduser("~/.openclaw/skills/google-places"))

import run as WTG

# Patch query_place_api_only and query_place_full with logging
_orig_api = WTG.query_place_api_only
_def_api_count = [0]
_def_full_count = [0]
_def_full_cache_hits = [0]
_def_full_cache_misses = [0]

def logged_api(place_id):
    t = time.time()
    result = _orig_api(place_id)
    _def_api_count[0] += 1
    print(f"[API  ] #{_def_api_count[0]} pid={place_id[:20]}... t={time.time()-t:.2f}s cache={'HIT' if place_id in WTG._QUERY_API_CACHE else 'MISS'}", flush=True)
    return result

_orig_full = WTG.query_place_full
def logged_full(place_id):
    t = time.time()
    cache_hit = place_id in WTG._QUERY_FULL_CACHE
    if cache_hit:
        _def_full_cache_hits[0] += 1
        print(f"[FULL ] #{_def_full_cache_hits[0]+_def_full_cache_misses[0]} pid={place_id[:20]}... t={time.time()-t:.4f}s CACHE_HIT", flush=True)
        return _def_full_cache_misses[0], WTG._QUERY_FULL_CACHE[place_id]
    _def_full_cache_misses[0] += 1
    result = _orig_full(place_id)
    print(f"[FULL ] #{_def_full_cache_hits[0]+_def_full_cache_misses[0]} pid={place_id[:20]}... t={time.time()-t:.2f}s CACHE_MISS", flush=True)
    return result

WTG.query_place_api_only = logged_api
WTG.query_place_full = logged_full

# Clear caches
WTG._QUERY_API_CACHE.clear()
WTG._QUERY_FULL_CACHE.clear()

params = WTG.parse_input("我要吃冰")
print(f"params={params}", flush=True)
print(f"FOOD_KEYWORDS includes 冰: {'冰' in WTG.FOOD_KEYWORDS}", flush=True)

t0 = time.time()
old_stdin = sys.stdin
sys.stdin = io.StringIO("")
result = WTG.search_and_detail(params, verbose=False)
sys.stdin = old_stdin
print(f"DONE in {time.time()-t0:.1f}s", flush=True)
print(f"API calls: {_def_api_count[0]}, FULL calls: misses={_def_full_cache_misses[0]} hits={_def_full_cache_hits[0]}", flush=True)
print(result[:800], flush=True)
