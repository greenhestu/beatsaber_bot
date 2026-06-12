#!/usr/bin/env python3
"""BeatLeader variant: top-240 score lists for ranked maps with 9 <= stars <= 11.

BeatLeader rate limit is 50 req / 10 s (x-rate-limit headers); we pace at
40 req / 10 s. count=100 is supported, so each map needs <= 3 pages.

  python3 fetch_bl.py            # catalog + scores in one go (resumable)
"""
import json
import os
import threading
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = "https://api.beatleader.xyz"
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
CATALOG_FILE = os.path.join(DATA, "bl_leaderboards.json")
SCORES_FILE = os.path.join(DATA, "bl_map_scores.jsonl")
MIN_STAR, MAX_STAR = 10.0, 12.0
TOP_N = 240
PER_PAGE = 100
RATE_MAX, RATE_WINDOW = 40, 10.0  # 40 req / 10 s (server allows 50)
WORKERS = 6

_lock = threading.Lock()
_req_times = []
_total = 0


def _slot():
    global _total
    while True:
        with _lock:
            now = time.monotonic()
            while _req_times and now - _req_times[0] > RATE_WINDOW:
                _req_times.pop(0)
            if len(_req_times) < RATE_MAX:
                _req_times.append(now)
                _total += 1
                return
            wait = RATE_WINDOW - (now - _req_times[0]) + 0.05
        time.sleep(wait)


def get(path, params=None):
    qs = "?" + "&".join(f"{k}={v}" for k, v in (params or {}).items())
    url = f"{BASE}{path}{qs}"
    for attempt in range(8):
        _slot()
        req = urllib.request.Request(url, headers={"User-Agent": "ss-topology/0.1"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(float(e.headers.get("Retry-After") or 11))
            elif e.code == 404:
                return None
            else:
                time.sleep(3 * (attempt + 1))
        except Exception:
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"giving up on {url}")


def fetch_catalog():
    if os.path.exists(CATALOG_FILE):
        return json.load(open(CATALOG_FILE))
    lbs, page = [], 1
    while True:
        d = get("/leaderboards", {"page": page, "count": 100, "type": "ranked",
                                  "stars_from": MIN_STAR, "stars_to": MAX_STAR})
        items = d["data"]
        if not items:
            break
        for l in items:
            s, df = l["song"], l["difficulty"]
            lbs.append({
                "id": l["id"], "song": s["name"], "author": s["author"],
                "mapper": s["mapper"], "diff": df["difficultyName"],
                "stars": df["stars"], "max_pp": None,
                "max_score": df.get("maxScore"), "plays": l.get("plays"),
                "hash": s["hash"], "njs": df.get("njs"), "nps": df.get("nps"),
                "speed_tags": df.get("speedTags"), "style_tags": df.get("styleTags"),
                "acc_rating": df.get("accRating"), "pass_rating": df.get("passRating"),
                "tech_rating": df.get("techRating"),
            })
        if len(lbs) >= d["metadata"]["total"]:
            break
        page += 1
    json.dump(lbs, open(CATALOG_FILE, "w"))
    print(f"BL catalog: {len(lbs)} ranked maps {MIN_STAR}-{MAX_STAR}*", flush=True)
    return lbs


def fetch_map_scores(lb):
    rows = []
    for page in range(1, TOP_N // PER_PAGE + 2):  # 3 pages for 240
        d = get(f"/leaderboard/{lb['id']}", {"page": page, "count": PER_PAGE})
        scores = (d or {}).get("scores") or []
        for s in scores:
            p = s.get("player") or {}
            rows.append({
                "player_id": s.get("playerId") or p.get("id"),
                "player_name": p.get("name"), "country": s.get("country"),
                "rank": s["rank"], "base": s["baseScore"],
                "mod": s["modifiedScore"], "pp": s.get("pp"),
                "acc": (s.get("accuracy") or 0) * 100,
                "modifiers": s.get("modifiers") or "",
                "bad": s.get("badCuts"), "miss": s.get("missedNotes"),
                "fc": s.get("fullCombo"),
            })
        if len(scores) < PER_PAGE or len(rows) >= TOP_N:
            break
    return lb["id"], rows[:TOP_N]


def main():
    os.makedirs(DATA, exist_ok=True)
    lbs = fetch_catalog()
    done = set()
    if os.path.exists(SCORES_FILE):
        with open(SCORES_FILE) as f:
            for line in f:
                try:
                    done.add(json.loads(line)["_lb"])
                except Exception:
                    pass
    todo = [l for l in lbs if l["id"] not in done]
    print(f"{len(done)} maps done, {len(todo)} to go "
          f"(~{len(todo) * 3} calls, ~{len(todo) * 3 / (RATE_MAX / RATE_WINDOW * 60):.0f} min)",
          flush=True)
    out = open(SCORES_FILE, "a")
    t0 = time.monotonic()
    n = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(fetch_map_scores, l): l for l in todo}
        for fut in as_completed(futs):
            lb_id, rows = fut.result()
            with _lock:
                out.write(json.dumps({"_lb": lb_id, "scores": rows}) + "\n")
                out.flush()
            n += 1
            if n % 50 == 0:
                el = time.monotonic() - t0
                print(f"{n}/{len(todo)} maps | {_total} reqs | "
                      f"{_total / el * 60:.0f} req/min", flush=True)
    out.close()
    print(f"DONE: {_total} requests this run", flush=True)


if __name__ == "__main__":
    main()
