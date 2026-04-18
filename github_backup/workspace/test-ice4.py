#!/usr/bin/env python3
"""快速 debug 版 run.py"""
import subprocess, json, sys, os, re, math, time

os.chdir(os.path.expanduser("~/.openclaw/skills/google-places"))
env = os.environ.copy()
env["GOOGLE_PLACES_API_KEY"] = os.environ.get("GOOGLE_PLACES_API_KEY", "")

DEFAULT_LAT = 24.18588146738243
DEFAULT_LNG = 120.66765935832942
DEFAULT_RADIUS_M = 1000
DEFAULT_MIN_RATING = 4.5
DEFAULT_MAX_RESULTS = 5

FOOD_KEYWORDS = [
    "火鍋","壽司","合菜","快炒","素食","港式","飲茶",
    "燒肉","燒烤","牛排","炸物","披薩","義大利麵",
    "咖哩","拉麵","烏龍麵","牛肉麵","蚵仔煎","肉圓",
    "滷肉飯","雞腿飯","便當","自助餐","buffet",
    "冰","早午餐","brunch","咖啡","甜點","蛋糕","冰淇淋",
    "剉冰","豆花","仙草","芋圓",
    "冰品","冰店","雪花冰","芒果冰","仙草凍",
    "芋圓","地瓜圓","湯圓","米苔目","愛玉","石花凍",
    "杏仁豆腐","米糕粥","甜湯","甜品","涼茶","青草茶",
    "楊枝甘露","燒仙草","冰剉冰","傳統冰",
]

def haversine(lat1,lng1,lat2,lng2):
    R = 6371000
    phi1,phi2 = math.radians(lat1),math.radians(lat2)
    dphi = math.radians(lat2-lat1)
    dlam = math.radians(lng2-lng1)
    a = math.sin(dphi/2)**2+math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    return 2*R*math.atan2(math.sqrt(a),math.sqrt(1-a))

def get_rating(c):
    try: return float(c.get("rating",0))
    except: return 0.0

keyword = "冰"
lat, lng = DEFAULT_LAT, DEFAULT_LNG
min_rating = DEFAULT_MIN_RATING
max_results = DEFAULT_MAX_RESULTS

t0 = time.time()
print(f"[{time.strftime('%H:%M:%S')}] Search...", flush=True)

# Step 2: search
args = ["goplaces","search",keyword,
        "--lat",str(lat),"--lng",str(lng),
        "--radius-m","1000",
        "--open-now","--min-rating","4.5",
        "--limit","20","--json"]
r = subprocess.run(args, capture_output=True, text=True, env=env, timeout=30)
out = r.stdout + r.stderr
all_lines = out.split("\n")
json_end_idx = None
for j in range(len(all_lines)-2,-1,-1):
    if all_lines[j].strip() == "]":
        json_end_idx = j
        break
candidates = json.loads("\n".join(all_lines[:json_end_idx+1]))
print(f"[{time.strftime('%H:%M:%S')}] Search done: {len(candidates)} in {time.time()-t0:.1f}s", flush=True)

# Step 3: filter sort
filtered = []
for c in candidates:
    if get_rating(c) < min_rating: continue
    loc = c.get("location",{})
    dist = haversine(lat,lng,loc.get("lat",0),loc.get("lng",0))
    c["_distance_m"] = dist
    filtered.append(c)
filtered.sort(key=lambda x: x["_distance_m"])
print(f"[{time.strftime('%H:%M:%S')}] Filtered: {len(filtered)}, top dist={filtered[0].get('_distance_m',0):.0f}m", flush=True)

# Check if food keyword
is_food = keyword in FOOD_KEYWORDS
print(f"[{time.strftime('%H:%M:%S')}] is_food={is_food}", flush=True)

# Top 5
top_results = filtered[:max_results]
print(f"[{time.strftime('%H:%M:%S')}] Processing {len(top_results)} places...", flush=True)

for i, place in enumerate(top_results):
    pid = place.get("place_id","")
    name = place.get("name","")
    t1 = time.time()
    print(f"[{time.strftime('%H:%M:%S')}] [{i+1}/5] {name}", flush=True)

    # details
    dr = subprocess.run(["goplaces","details",pid,"--reviews","--json"],
                        capture_output=True, text=True, env=env, timeout=30)
    dt = time.time()-t1
    print(f"[{time.strftime('%H:%M:%S')}]   details={dt:.1f}s rc={dr.returncode}", flush=True)

    # priceRange (may fail on SSL)
    t2 = time.time()
    pr = None
    try:
        import urllib.request
        key = env["GOOGLE_PLACES_API_KEY"]
        url = f"https://places.googleapis.com/v1/places/{pid}?fields=priceRange&key={key}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            prd = json.loads(resp.read())
        pr = prd.get("priceRange")
    except Exception as e:
        pass
    prt = time.time()-t2
    print(f"[{time.strftime('%H:%M:%S')}]   priceRange={prt:.1f}s pr={pr}", flush=True)

    total = time.time()-t1
    print(f"[{time.strftime('%H:%M:%S')}]   TOTAL={total:.1f}s", flush=True)

print(f"[{time.strftime('%H:%M:%S')}] ALL DONE in {time.time()-t0:.1f}s total", flush=True)
