#!/usr/bin/env python3
"""ScoreSaber user classification — query.

Given a player (must be within the fetched top 3000), find HIGHER-pp players
whose top-100 pp maps are most similar to the target's. Useful as "who should
I look at to decide what to play next".

Similarity = cosine over pp-weighted song vectors (each user's top-100 maps,
weighted by their pp on the map), plus common-map count.

Usage: similar.py <player_id | player_name> [topN] [--playlist=<path>]
  --playlist writes farm candidates (top-3 similar users' high-pp maps the
  target hasn't played) as a Beat Saber playlist (.bplist). Song hashes are
  looked up from ../ss_maps/data/leaderboards.json.
"""
import json
import math
import os
import sys
import urllib.error
import urllib.request
from collections import defaultdict

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
PLAYERS_FILE = os.path.join(DATA, "players.json")
SCORES_FILE = os.path.join(DATA, "top_scores.jsonl")
MIN_COMMON = 5
# position weight inside the top-100: w = DECAY^index (0=best score).
# 0.965 matches ScoreSaber's own pp weighting — #1:1.0, #10:0.73, #50:0.17,
# #100:0.03 — heavily top-focused. Use 0.99 for a gentler curve.
WEIGHT_DECAY = 0.965


def load():
    players = {p["id"]: p for p in json.load(open(PLAYERS_FILE))}
    vecs, raw_scores, songs = {}, {}, {}
    with open(SCORES_FILE) as f:
        for line in f:
            rec = json.loads(line)
            v, raw = {}, {}
            for i, s in enumerate(rec["scores"]):  # scores are pp-desc sorted
                v[s["lb_id"]] = s["pp"] * (WEIGHT_DECAY ** i)
                raw[s["lb_id"]] = s["pp"]
                songs[s["lb_id"]] = (s["song"], s["author"], s["stars"])
            vecs[rec["_player"]] = v
            raw_scores[rec["_player"]] = raw
    return players, vecs, raw_scores, songs


def fetch_plus_one_pp(player_id):
    url = f"https://scoresaber.com/api/v2/players/{player_id}"
    req = urllib.request.Request(url, headers={"User-Agent": "beatsaber_bot/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode())
        value = (data.get("stats") or {}).get("plusOnePP")
        return float(value) if value is not None else None
    except (OSError, ValueError, TypeError, urllib.error.HTTPError):
        return None


def cosine(a, b):
    common = a.keys() & b.keys()
    if not common:
        return 0.0, 0
    dot = sum(a[k] * b[k] for k in common)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb), len(common)


def write_playlist(path, title, lb_ids, songs):
    cat_file = os.path.join(os.path.dirname(DATA), "..", "ss_maps", "data",
                            "leaderboards.json")
    try:
        cat = {l["id"]: l for l in json.load(open(cat_file))}
    except FileNotFoundError:
        cat = {}
    entries = []
    for lb in lb_ids:
        c = cat.get(lb)
        if not c or not c.get("hash"):
            continue
        d = c["diff"]
        diff_name = d.split("_")[1] if d.startswith("_") else d
        entries.append({
            "hash": c["hash"],
            "songName": f'{c["song"]} - {c["author"]}',
            "difficulties": [{"characteristic": "Standard", "name": diff_name}],
        })
    with open(path, "w") as f:
        json.dump({"playlistTitle": title, "playlistAuthor": "beatsaber_bot",
                   "songs": entries, "image": ""}, f)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    query = args[0]
    top_n = int(args[1]) if len(args) > 1 else 15

    players, vecs, raw_scores, songs = load()

    # resolve target by id, else by (case-insensitive) name
    target = players.get(query)
    if target is None:
        matches = [p for p in players.values()
                   if p["name"].lower() == query.lower()]
        if not matches:
            matches = [p for p in players.values()
                       if query.lower() in p["name"].lower()]
        if not matches:
            sys.exit(f"player '{query}' not in fetched top {len(players)}")
        target = min(matches, key=lambda p: p["rank"])
    tv = vecs.get(target["id"])
    if not tv:
        sys.exit(f"no scores fetched for {target['name']}")
    plus_one_pp = fetch_plus_one_pp(target["id"])
    if plus_one_pp is None:
        sys.exit("could not retrieve the target player's +1PP threshold")

    print(f"\nTarget: #{target['rank']} {target['name']} ({target['country']}) "
          f"{target['pp']:.0f}pp — comparing against higher-pp players\n")
    print(f"ScoreSaber +1PP 기준: {plus_one_pp:.2f} raw pp 초과\n")

    out = []
    for pid, v in vecs.items():
        p = players.get(pid)
        if p is None or p["pp"] <= target["pp"] or pid == target["id"]:
            continue
        sim, nc = cosine(tv, v)
        if nc < MIN_COMMON:
            continue
        out.append((sim, nc, p))
    out.sort(key=lambda x: -x[0])

    print(f"{'cos':>6} {'common':>6} {'rank':>6} {'pp':>8}  player")
    for sim, nc, p in out[:top_n]:
        print(f"{sim:6.3f} {nc:6d} {p['rank']:6d} {p['pp']:8.0f}  "
              f"{p['name']} ({p['country']})")

    if out:
        compared = out[:top_n]
        occurrences = defaultdict(list)
        disqualified = set()
        for _, _, player in compared:
            for lb, raw_pp in raw_scores[player["id"]].items():
                if lb in tv:
                    continue
                if raw_pp <= plus_one_pp:
                    disqualified.add(lb)
                else:
                    occurrences[lb].append((player["name"], raw_pp))

        candidates = [
            (lb, values)
            for lb, values in occurrences.items()
            if len(values) >= 2 and lb not in disqualified
        ]
        candidates.sort(key=lambda item: (
            -len(item[1]),
            -min(pp for _, pp in item[1]),
            -sum(pp for _, pp in item[1]) / len(item[1]),
        ))

        print(f"\n유사 유저 {len(compared)}명에게 반복 등장하고 모두 "
              f"{plus_one_pp:.2f}pp를 넘긴 맵:")
        if not candidates:
            print("  조건을 만족하는 맵이 없습니다.")
        for lb, values in candidates[:8]:
            song, author, stars = songs[lb]
            pp_values = [pp for _, pp in values]
            print(f"  {len(values)}/{len(compared)}명  "
                  f"{min(pp_values):.1f}-{max(pp_values):.1f}pp  "
                  f"{stars:5.2f}* {song} ({author}) [lb:{lb}]")

        pl = next((a for a in sys.argv if a.startswith("--playlist=")), None)
        if pl:
            picks = [lb for lb, _ in candidates[:20]]
            write_playlist(pl.split("=", 1)[1],
                           f"Farm picks for {target['name']}", picks, songs)


if __name__ == "__main__":
    main()
