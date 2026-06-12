#!/usr/bin/env python3
"""Per-map approach: for every ranked leaderboard with stars >= 7.13 (~300pp),
fetch the top-1000 score list (12 scores/page, max 84 pages/map).

Rate-limited under 400 req/min (token bucket at 370/min). Resumable.

  python3 fetch_maps.py catalog   # fetch leaderboard catalog, print call estimate
  python3 fetch_maps.py scores    # fetch top-1000 scores for every map (resumable)
"""
import json
import math
import os
import sys
import threading
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = "https://scoresaber.com/api"
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
CATALOG_FILE = os.path.join(DATA, "leaderboards.json")
SCORES_FILE = os.path.join(DATA, "map_scores.jsonl")
MIN_STAR = 7.13  # ~300pp (pp = stars * 42.117 at SS+) — catalog floor
FETCH_MIN_STAR = 9.0   # star window actually fetched
FETCH_MAX_STAR = 11.0
TOP_N = 240
PER_PAGE = 12
RATE_PER_MIN = 370
WORKERS = 8

_lock = threading.Lock()
_req_times = []
_total_requests = 0


def _acquire_slot():
    global _total_requests
    while True:
        with _lock:
            now = time.monotonic()
            while _req_times and now - _req_times[0] > 60.0:
                _req_times.pop(0)
            if len(_req_times) < RATE_PER_MIN:
                _req_times.append(now)
                _total_requests += 1
                return
            wait = 60.0 - (now - _req_times[0]) + 0.05
        time.sleep(wait)


def get(path, params=None):
    qs = "?" + "&".join(f"{k}={v}" for k, v in (params or {}).items())
    url = f"{BASE}{path}{qs}"
    for attempt in range(8):
        _acquire_slot()
        req = urllib.request.Request(url, headers={"User-Agent": "ss-topology/0.1"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                ra = float(e.headers.get("Retry-After") or 15)
                time.sleep(ra)
            elif e.code == 404:
                return None
            else:
                time.sleep(3 * (attempt + 1))
        except Exception:
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"giving up on {url}")


def pages_needed(plays):
    return math.ceil(min(TOP_N, max(plays, 0)) / PER_PAGE)


def fetch_catalog():
    lbs = []
    page = 1
    while True:
        d = get("/leaderboards", {"ranked": "true", "minStar": MIN_STAR,
                                  "page": page, "withMetadata": "true"})
        items = d["leaderboards"]
        if not items:
            break
        for l in items:
            lbs.append({
                "id": l["id"], "song": l["songName"],
                "author": l["songAuthorName"], "mapper": l["levelAuthorName"],
                "diff": l["difficulty"]["difficultyRaw"], "stars": l["stars"],
                "max_pp": l["maxPP"], "max_score": l["maxScore"],
                "plays": l["plays"], "hash": l["songHash"],
            })
        total = d["metadata"]["total"]
        if page % 20 == 0:
            print(f"catalog page {page} ({len(lbs)}/{total})", flush=True)
        if len(lbs) >= total:
            break
        page += 1
    with open(CATALOG_FILE, "w") as f:
        json.dump(lbs, f)
    calls = sum(pages_needed(l["plays"]) for l in lbs)
    print(f"\n{len(lbs)} leaderboards >= {MIN_STAR}*")
    print(f"score-fetch calls needed: {calls} "
          f"(~{calls / RATE_PER_MIN:.0f} min at {RATE_PER_MIN}/min)")
    return lbs


def fetch_map_scores(lb):
    n_pages = pages_needed(lb["plays"])
    rows = []
    for page in range(1, n_pages + 1):
        d = get(f"/leaderboard/by-id/{lb['id']}/scores", {"page": page})
        scores = (d or {}).get("scores") or []
        if not scores:
            break
        for s in scores:
            p = s["leaderboardPlayerInfo"]
            rows.append({
                "player_id": p["id"], "player_name": p["name"],
                "country": p.get("country"),
                "rank": s["rank"], "base": s["baseScore"],
                "mod": s["modifiedScore"], "pp": s["pp"],
                "modifiers": s.get("modifiers") or "",
                "bad": s.get("badCuts"), "miss": s.get("missedNotes"),
                "fc": s.get("fullCombo"),
            })
        if len(rows) >= TOP_N:
            break
    return lb["id"], rows


def fetch_scores():
    with open(CATALOG_FILE) as f:
        lbs = json.load(f)
    lbs = [l for l in lbs if FETCH_MIN_STAR <= l["stars"] <= FETCH_MAX_STAR]
    done = set()
    if os.path.exists(SCORES_FILE):
        with open(SCORES_FILE) as f:
            for line in f:
                try:
                    done.add(json.loads(line)["_lb"])
                except Exception:
                    pass
    todo = [l for l in lbs if l["id"] not in done]
    total_calls = sum(pages_needed(l["plays"]) for l in todo)
    print(f"{len(done)} maps done, {len(todo)} to go (~{total_calls} calls, "
          f"~{total_calls / RATE_PER_MIN:.0f} min)", flush=True)

    out = open(SCORES_FILE, "a")
    t0 = time.monotonic()
    n_done = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(fetch_map_scores, l): l for l in todo}
        for fut in as_completed(futs):
            lb_id, rows = fut.result()
            with _lock:
                out.write(json.dumps({"_lb": lb_id, "scores": rows}) + "\n")
                out.flush()
            n_done += 1
            if n_done % 50 == 0:
                el = time.monotonic() - t0
                rate = _total_requests / el * 60 if el > 0 else 0
                eta = (total_calls - _total_requests) / max(rate, 1)
                print(f"{n_done}/{len(todo)} maps | {_total_requests} reqs | "
                      f"{rate:.0f} req/min | eta {eta:.0f} min", flush=True)
    out.close()
    print(f"DONE: {_total_requests} requests this run", flush=True)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "catalog"
    os.makedirs(DATA, exist_ok=True)
    if mode == "catalog":
        fetch_catalog()
    elif mode == "scores":
        fetch_scores()
