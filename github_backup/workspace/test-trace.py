#!/usr/bin/env python3
"""診斷 run.py 各階段時間"""
import sys, os, time, io

sys.path.insert(0, os.path.expanduser("~/.openclaw/skills/where-to-go/scripts"))
os.environ["PYTHONUNBUFFERED"] = "1"
os.chdir(os.path.expanduser("~/.openclaw/skills/google-places"))

import run as WTG

params = WTG.parse_input("我要吃冰")

# Patch search_and_detail to add timing
orig_search = WTG.search_and_detail

def timed_search(params, verbose=True):
    t0 = time.time()
    # Step 2: expansion
    t2 = time.time()
    candidates = []
    for radius in WTG.EXPANSION_RADII:
        if radius < params["radius_m"]: continue
        r = WTG.goplaces_search(params["keyword"], params["lat"], params["lng"],
                                radius, params["min_rating"])
        candidates = r if isinstance(r, list) else r.get("places", []) if isinstance(r, dict) else []
        print(f"[{time.time()-t0:.1f}s] search radius={radius}m -> {len(candidates)} candidates", flush=True)
        if len(candidates) >= 5: break
        if radius >= 50000: break
    print(f"[{time.time()-t0:.1f}s] Step2 done, {len(candidates)} candidates", flush=True)

    # Step 3: filter
    t3 = time.time()
    filtered = WTG.filter_and_sort(candidates, params["lat"], params["lng"], params["min_rating"])
    print(f"[{time.time()-t0:.1f}s] Step3 done, {len(filtered)} filtered", flush=True)

    # Food filtering (simplified)
    food_kw = params.get("food_kw")
    if food_kw:
        for place in filtered:
            pid = WTG.get_place_id(place)
            if pid:
                api_data = WTG.query_place_api_only(pid)
                place["_api_data"] = api_data
                if api_data and WTG.place_mentions_food(api_data, food_kw):
                    place["_match"] = True
                else:
                    place["_match"] = False
        print(f"[{time.time()-t0:.1f}s] Food filter done", flush=True)

    # Select top 5
    top_results = filtered[:5]
    print(f"[{time.time()-t0:.1f}s] Top {len(top_results)} selected", flush=True)

    # Step 4: details for each
    for i, place in enumerate(top_results):
        pid = WTG.get_place_id(place)
        t_detail = time.time()
        api_data = WTG.query_place_api_only(pid) if pid else None
        print(f"[{time.time()-t0:.1f}s] Place {i+1} details={time.time()-t_detail:.1f}s", flush=True)

        t_qfull = time.time()
        _, raw_output = WTG.query_place_full(pid) if pid else (None, "")
        print(f"[{time.time()-t0:.1f}s] Place {i+1} query_full={time.time()-t_qfull:.1f}s", flush=True)

    print(f"[{time.time()-t0:.1f}s] TOTAL", flush=True)
    return "TRACE DONE"

print("params:", params, flush=True)
result = timed_search(params)
print(result, flush=True)
