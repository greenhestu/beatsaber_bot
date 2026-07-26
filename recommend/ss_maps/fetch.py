#!/usr/bin/env python3
"""Per-map approach: fetch leaderboard user distributions for top-star maps.

Default policy: build a ranked leaderboard catalog, select up to the map
limit (default 3,600), then fetch each map's top-240 score list. The ScoreSaber
returns 12 scores/page, so this is intentionally paced well below the public
400 req/min limit. Resumable. After the top-star range is complete, the
remaining ranked maps can be fetched with one page each so every ranked map has
at least ranks 1-12 stored when the API exposes them.

  python3 fetch.py catalog   # fetch leaderboard catalog, print call estimate
  python3 fetch.py scores              # fetch top scores for selected maps
  python3 fetch.py scores-rest-page1   # fetch one page for maps after the limit
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
DEFAULT_SCORES_FILE = os.path.join(DATA, "map_scores.jsonl")
SCORES_FILE = os.environ.get("SS_MAPS_SCORES_FILE", DEFAULT_SCORES_FILE)
EXTRA_DONE_FILES = [p for p in os.environ.get("SS_MAPS_DONE_FILES", "").split(os.pathsep) if p]
DONE_FILES = list(dict.fromkeys([DEFAULT_SCORES_FILE, SCORES_FILE] + EXTRA_DONE_FILES))
MIN_STAR = float(os.environ.get("SS_MAPS_CATALOG_MIN_STAR", "0"))
MAP_LIMIT = int(os.environ.get("SS_MAPS_MAP_LIMIT", "3600"))
TOP_N = int(os.environ.get("SS_MAPS_TOP_N", "240"))
PER_PAGE = 12
RATE_WINDOW = float(os.environ.get("SS_MAPS_RATE_WINDOW", "10"))
RATE_PER_MIN = int(os.environ.get("SS_MAPS_RATE_PER_MIN", "0")) or 0
RATE_PER_WINDOW = int(os.environ.get("SS_MAPS_RATE_PER_WINDOW", "0")) or 0
if RATE_PER_WINDOW <= 0:
    if RATE_PER_MIN > 0:
        RATE_PER_WINDOW = max(1, round(RATE_PER_MIN * RATE_WINDOW / 60))
    else:
        RATE_PER_WINDOW = 20
if RATE_PER_MIN <= 0:
    RATE_PER_MIN = max(1, round(RATE_PER_WINDOW * 60 / RATE_WINDOW))
WORKERS = int(os.environ.get("SS_MAPS_WORKERS", "4"))

_lock = threading.Lock()
_req_times = []
_total_requests = 0


def _acquire_slot():
    global _total_requests
    while True:
        with _lock:
            now = time.monotonic()
            while _req_times and now - _req_times[0] > RATE_WINDOW:
                _req_times.pop(0)
            if len(_req_times) < RATE_PER_WINDOW:
                _req_times.append(now)
                _total_requests += 1
                return
            wait = RATE_WINDOW - (now - _req_times[0]) + 0.05
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


def pages_needed(plays, top_n=TOP_N):
    return math.ceil(min(top_n, max(plays, 0)) / PER_PAGE)


def ranked_maps(lbs):
    return sorted(
        lbs,
        key=lambda l: (float(l.get("stars") or 0), float(l.get("max_pp") or 0), int(l.get("plays") or 0)),
        reverse=True,
    )


def selected_maps(lbs):
    return ranked_maps(lbs)[:MAP_LIMIT]


def remaining_maps_after_limit(lbs):
    return ranked_maps(lbs)[MAP_LIMIT:]


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
                "created_date": l.get("createdDate"),
                "ranked_date": l.get("rankedDate"),
                "qualified_date": l.get("qualifiedDate"),
                "loved_date": l.get("lovedDate"),
            })
        total = d["metadata"]["total"]
        if page % 20 == 0:
            print(f"catalog page {page} ({len(lbs)}/{total})", flush=True)
        if len(lbs) >= total:
            break
        page += 1
    with open(CATALOG_FILE, "w") as f:
        json.dump(lbs, f)
    selected = selected_maps(lbs)
    calls = sum(pages_needed(l["plays"]) for l in selected)
    print(f"\n{len(lbs)} leaderboards >= {MIN_STAR}*")
    print(f"selected top-star maps: {len(selected)}")
    if selected:
        print(f"selected star range: {selected[-1]['stars']:.2f}* - {selected[0]['stars']:.2f}*")
    print(f"score-fetch calls needed for selected maps: {calls} "
          f"(~{calls / RATE_PER_MIN:.0f} min at {RATE_PER_WINDOW}/{RATE_WINDOW:.0f}s)")
    return lbs


def fetch_map_scores(lb, top_n=TOP_N):
    n_pages = pages_needed(lb["plays"], top_n)
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
        if len(rows) >= top_n:
            break
    return lb["id"], rows


def done_map_ids():
    done = set()
    for path in DONE_FILES:
        if not os.path.exists(path):
            continue
        with open(path) as f:
            for line in f:
                try:
                    done.add(json.loads(line)["_lb"])
                except Exception:
                    pass
    return done


def fetch_scores_for_maps(lbs, top_n, label):
    done = done_map_ids()
    todo = [l for l in lbs if l["id"] not in done]
    done_in_scope = len(lbs) - len(todo)
    total_calls = sum(pages_needed(l["plays"], top_n) for l in todo)
    print(f"writing scores to: {SCORES_FILE}", flush=True)
    print(f"{done_in_scope}/{len(lbs)} {label} maps done, {len(todo)} to go (~{total_calls} calls, "
          f"~{total_calls / RATE_PER_MIN:.0f} min at {RATE_PER_WINDOW}/{RATE_WINDOW:.0f}s)", flush=True)

    out = open(SCORES_FILE, "a")
    t0 = time.monotonic()
    n_done = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(fetch_map_scores, l, top_n): l for l in todo}
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


def fetch_scores():
    with open(CATALOG_FILE) as f:
        lbs = json.load(f)
    fetch_scores_for_maps(selected_maps(lbs), TOP_N, "selected")


def fetch_rest_page1():
    with open(CATALOG_FILE) as f:
        lbs = json.load(f)
    rest = remaining_maps_after_limit(lbs)
    if rest:
        print(f"rest star range: {rest[-1]['stars']:.2f}* - {rest[0]['stars']:.2f}*", flush=True)
    fetch_scores_for_maps(rest, PER_PAGE, "rest-page1")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "catalog"
    os.makedirs(DATA, exist_ok=True)
    if mode == "catalog":
        fetch_catalog()
    elif mode == "scores":
        fetch_scores()
    elif mode in ("scores-rest-page1", "scores-tail12", "tail12"):
        fetch_rest_page1()
