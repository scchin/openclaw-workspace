#!/usr/bin/env python3
"""測試 run.py 完整輸出格式化"""
import subprocess, json, sys, os, re, math, time

os.chdir(os.path.expanduser("~/.openclaw/skills/google-places"))
env = os.environ.copy()
env["GOOGLE_PLACES_API_KEY"] = os.environ.get("GOOGLE_PLACES_API_KEY", "")
env["PYTHONUNBUFFERED"] = "1"

# 透通了 search_and_detail 的流程
sys.path.insert(0, os.path.expanduser("~/.openclaw/skills/where-to-go/scripts"))

# 直接 import 需要的部分
import run as WTG
params = WTG.parse_input("我要吃冰")
print(f"params={params}", flush=True)

print("Calling search_and_detail...", flush=True)
t0 = time.time()
# Redirect stdin to make sure nothing blocks
import io
old_stdin = sys.stdin
sys.stdin = io.StringIO("")
result = WTG.search_and_detail(params)
sys.stdin = old_stdin
print(f"DONE in {time.time()-t0:.1f}s", flush=True)
print("RESULT:", result[:200], flush=True)
