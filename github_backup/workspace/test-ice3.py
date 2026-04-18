#!/usr/bin/env python3
import subprocess, json, sys, os, time, signal

os.chdir(os.path.expanduser("~/.openclaw/skills/google-places"))
env = os.environ.copy()
env["GOOGLE_PLACES_API_KEY"] = os.environ.get("GOOGLE_PLACES_API_KEY", "")

keyword = "冰"
lat, lng = 24.18588146738243, 120.66765935832942

# Simulate what run.py does for Step 2
print(f"[{time.strftime('%H:%M:%S')}] === Step 2: search ===", flush=True)
args = [
    "goplaces", "search", keyword,
    "--lat", str(lat), "--lng", str(lng),
    "--radius-m", "1000",
    "--open-now", "--min-rating", "4.5",
    "--limit", "20", "--json",
]
t0 = time.time()
r = subprocess.run(args, capture_output=True, text=True, env=env, timeout=30)
print(f"[{time.strftime('%H:%M:%S')}] search done in {time.time()-t0:.1f}s", flush=True)
out = r.stdout + r.stderr
all_lines = out.split("\n")
json_end_idx = None
for j in range(len(all_lines) - 2, -1, -1):
    if all_lines[j].strip() == "]":
        json_end_idx = j
        break
candidates = json.loads("\n".join(all_lines[:json_end_idx + 1]))
print(f"[{time.strftime('%H:%M:%S')}] Got {len(candidates)} candidates", flush=True)

# Simulate filter_and_sort
import math
def haversine(lat1, lng1, lat2, lng2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))

center_lat, center_lng = lat, lng
min_rating = 4.5
filtered = []
for c in candidates:
    if c.get("rating", 0) < min_rating: continue
    loc = c.get("location", {})
    dist = haversine(center_lat, center_lng, loc.get("lat", 0), loc.get("lng", 0))
    c["_distance_m"] = dist
    filtered.append(c)
filtered.sort(key=lambda x: x["_distance_m"])
print(f"[{time.strftime('%H:%M:%S')}] Filtered to {len(filtered)} (distances assigned)", flush=True)

# Take top 5
top_results = filtered[:5]
print(f"[{time.strftime('%H:%M:%S')}] Processing {len(top_results)} places...", flush=True)

# Now for each top result, call query_place_api_only
for i, place in enumerate(top_results):
    place_id = place.get("place_id")
    print(f"[{time.strftime('%H:%M:%S')}] [{i+1}/5] details for {place.get('name')} (pid={place_id[:20]}...)", flush=True)
    t1 = time.time()
    # details
    dr = subprocess.run(
        ["goplaces", "details", place_id, "--reviews", "--json"],
        capture_output=True, text=True, env=env, timeout=30
    )
    print(f"[{time.strftime('%H:%M:%S')}]   details took {time.time()-t1:.1f}s, rc={dr.returncode}", flush=True)
    # price range
    t2 = time.time()
    try:
        import urllib.request
        key = env["GOOGLE_PLACES_API_KEY"]
        url = f"https://places.googleapis.com/v1/places/{place_id}?fields=priceRange&key={key}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            pr_data = json.loads(resp.read())
        print(f"[{time.strftime('%H:%M:%S')}]   priceRange took {time.time()-t2:.1f}s: {pr_data.get('priceRange')}", flush=True)
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}]   priceRange error: {e}", flush=True)
    total = time.time() - t1
    print(f"[{time.strftime('%H:%M:%S')}]   TOTAL for {place.get('name')}: {total:.1f}s", flush=True)

print(f"[{time.strftime('%H:%M:%S')}] === ALL DONE ===", flush=True)
