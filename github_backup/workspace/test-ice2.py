#!/usr/bin/env python3
import subprocess, json, sys, os, time

os.chdir(os.path.expanduser("~/.openclaw/skills/google-places"))
env = os.environ.copy()
env["GOOGLE_PLACES_API_KEY"] = os.environ.get("GOOGLE_PLACES_API_KEY", "")

keyword = "冰"
lat, lng = 24.18588146738243, 120.66765935832942
radius_m = 1000
min_rating = 4.5

print(f"[{time.strftime('%H:%M:%S')}] Search...", flush=True)
args = [
    "goplaces", "search", keyword,
    "--lat", str(lat), "--lng", str(lng),
    "--radius-m", str(radius_m),
    "--open-now", "--min-rating", str(min_rating),
    "--limit", "20", "--json",
]
r = subprocess.run(args, capture_output=True, text=True, env=env, timeout=30)
out = r.stdout + r.stderr
all_lines = out.split("\n")
json_end_idx = None
for j in range(len(all_lines) - 2, -1, -1):
    if all_lines[j].strip() == "]":
        json_end_idx = j
        break
json_text = "\n".join(all_lines[:json_end_idx + 1])
data = json.loads(json_text)
print(f"[{time.strftime('%H:%M:%S')}] Got {len(data)} results", flush=True)

# Test details call for first place
place_id = data[0]["place_id"]
print(f"[{time.strftime('%H:%M:%S')}] Details for: {data[0]['name']}", flush=True)
dr = subprocess.run(
    ["goplaces", "details", place_id, "--reviews", "--json"],
    capture_output=True, text=True, env=env, timeout=30
)
print(f"[{time.strftime('%H:%M:%S')}] details returncode={dr.returncode}", flush=True)
print(f"details stdout lines: {len(dr.stdout.splitlines())}", flush=True)
print(f"details stderr: {dr.stderr[:200]}", flush=True)

# Parse JSON from details
dout = dr.stdout.strip()
lines = dout.split("\n")
json_start = None
for i, l in enumerate(lines):
    if l.strip().startswith("{"):
        json_start = i
        break
if json_start is not None:
    json_part = "\n".join(lines[json_start:])
    try:
        ddata = json.loads(json_part)
        reviews = ddata.get("reviews", [])
        print(f"[{time.strftime('%H:%M:%S')}] Reviews: {len(reviews)}", flush=True)
    except Exception as e:
        print(f"JSON error: {e}", flush=True)
        print(f"First 200: {json_part[:200]}", flush=True)

print(f"[{time.strftime('%H:%M:%S')}] DONE", flush=True)
