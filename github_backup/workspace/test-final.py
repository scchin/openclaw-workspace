#!/usr/bin/env python3
"""直接測試 cache 後的 search_and_detail"""
import sys, os, time, io

sys.path.insert(0, os.path.expanduser("~/.openclaw/skills/where-to-go/scripts"))
os.environ["PYTHONUNBUFFERED"] = "1"
os.chdir(os.path.expanduser("~/.openclaw/skills/google-places"))

import run as WTG

# Clear caches
WTG._QUERY_API_CACHE.clear()
WTG._QUERY_FULL_CACHE.clear()

params = WTG.parse_input("我要吃冰")
print(f"params={params}", flush=True)

t0 = time.time()
old_stdin = sys.stdin
sys.stdin = io.StringIO("")
result = WTG.search_and_detail(params, verbose=True)
sys.stdin = old_stdin
print(f"DONE in {time.time()-t0:.1f}s", flush=True)
print("RESULT:")
print(result[:1000], flush=True)
