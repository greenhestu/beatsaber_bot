#!/usr/bin/env python3
"""ScoreSaber user classification — data fetch.

Top 3000 global players, and each player's top-100 pp scores (1 call/player).
~3060 calls total, paced at 370 req/min (< 400/min limit). Resumable.

  python3 fetch.py
"""
import json
import os
import threading
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = "https://scoresaber.com/api"
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
PLAYERS_FILE = os.path.join(DATA, "players.json")
SCORES_FILE = os.path.join(DATA, "top_scores.jsonl")
N_PLAYERS = 3000
RATE_PER_MIN = 370
WORKERS = 8

_lock = threading.Lock()
_req_times = []
_total = 0


def _slot():
    global _total
    while True:
        with _lock:
            now = time.monotonic()
            while _req_times and now - _req_times[0] > 60.0:
                _req_times.pop(0)
            if len(_req_times) < RATE_PER_MIN:
                _req_times.append(now)
                _total += 1
                return
            wait = 60.0 - (now - _req_times[0]) + 0.05
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
                time.sleep(float(e.headers.get("Retry-After") or 15))
            elif e.code == 404:
                return None
            else:
                time.sleep(3 * (attempt + 1))
        except Exception:
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"giving up on {url}")


def fetch_players():
    if os.path.exists(PLAYERS_FILE):
        return json.load(open(PLAYERS_FILE))
    players = []
    for page in range(1, N_PLAYERS // 50 + 1):
        d = get("/players", {"page": page})
        for p in d["players"]:
            players.append({"id": p["id"], "name": p["name"], "rank": p["rank"],
                            "pp": p["pp"], "country": p["country"]})
        if page % 10 == 0:
            print(f"players page {page}/{N_PLAYERS // 50}", flush=True)
    json.dump(players, open(PLAYERS_FILE, "w"))
    return players


def fetch_top100(player):
    d = get(f"/player/{player['id']}/scores",
            {"sort": "top", "limit": 100, "page": 1})
    rows = []
    for ps in (d or {}).get("playerScores") or []:
        s, lb = ps["score"], ps["leaderboard"]
        rows.append({
            "lb_id": lb["id"], "song": lb["songName"],
            "author": lb["songAuthorName"], "mapper": lb["levelAuthorName"],
            "diff": lb["difficulty"]["difficultyRaw"], "stars": lb["stars"],
            "pp": s["pp"], "rank_on_map": s["rank"],
            "modifiers": s.get("modifiers") or "",
        })
    return player["id"], rows


def main():
    os.makedirs(DATA, exist_ok=True)
    players = fetch_players()
    print(f"{len(players)} players", flush=True)
    done = set()
    if os.path.exists(SCORES_FILE):
        with open(SCORES_FILE) as f:
            for line in f:
                try:
                    done.add(json.loads(line)["_player"])
                except Exception:
                    pass
    todo = [p for p in players if p["id"] not in done]
    print(f"{len(done)} done, {len(todo)} to go "
          f"(~{len(todo)} calls, ~{len(todo) / RATE_PER_MIN:.0f} min)", flush=True)
    out = open(SCORES_FILE, "a")
    t0 = time.monotonic()
    n = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(fetch_top100, p): p for p in todo}
        for fut in as_completed(futs):
            pid, rows = fut.result()
            with _lock:
                out.write(json.dumps({"_player": pid, "scores": rows}) + "\n")
                out.flush()
            n += 1
            if n % 200 == 0:
                el = time.monotonic() - t0
                print(f"{n}/{len(todo)} players | {_total} reqs | "
                      f"{_total / el * 60:.0f} req/min", flush=True)
    out.close()
    print(f"DONE: {_total} requests this run", flush=True)


if __name__ == "__main__":
    main()
