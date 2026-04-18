#!/usr/bin/env python3
import subprocess, json, sys, os, time

os.chdir(os.path.expanduser("~/.openclaw/skills/google-places"))

env = os.environ.copy()
env["GOOGLE_PLACES_API_KEY"] = os.environ.get("GOOGLE_PLACES_API_KEY", "")

keyword = "冰"
lat, lng = 24.18588146738243, 120.66765935832942
radius_m = 1000
min_rating = 4.5

print(f"[{time.strftime('%H:%M:%S')}] Step 1: search", flush=True)
args = [
    "goplaces", "search", keyword,
    "--lat", str(lat), "--lng", str(lng),
    "--radius-m", str(radius_m),
    "--open-now", "--min-rating", str(min_rating),
    "--limit", "20", "--json",
]
print(f"[{time.strftime('%H:%M:%S')}] Running: {' '.join(args)}", flush=True)
r = subprocess.run(args, capture_output=True, text=True, env=env, timeout=30)
print(f"[{time.strftime('%H:%M:%S')}] search done, returncode={r.returncode}", flush=True)
print(f"stdout lines: {len(r.stdout.splitlines())}", flush=True)
print(f"stderr: {r.stderr[:200]}", flush=True)

out = r.stdout + r.stderr
all_lines = out.split("\n")
json_end_idx = None
for j in range(len(all_lines) - 2, -1, -1):
    if all_lines[j].strip() == "]":
        json_end_idx = j
        break
if json_end_idx is not None:
    json_text = "\n".join(all_lines[:json_end_idx + 1])
    try:
        data = json.loads(json_text)
        print(f"[{time.strftime('%H:%M:%S')}] Parsed {len(data)} results", flush=True)
        for item in data[:3]:
            print(f"  - {item.get('name')} ({item.get('place_id')}) rating={item.get('rating')}", flush=True)
    except Exception as e:
        print(f"JSON parse error: {e}", flush=True)
        print(f"First 300 chars of output: {out[:300]}", flush=True)
else:
    print("Could not find end of JSON array", flush=True)
    print(f"Output: {out[:500]}", flush=True)

print(f"[{time.strftime('%H:%M:%S')}] DONE", flush=True)
