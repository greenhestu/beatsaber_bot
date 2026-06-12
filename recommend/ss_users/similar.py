#!/usr/bin/env python3
"""ScoreSaber user classification — query.

Given a player (must be within the fetched top 3000), find HIGHER-pp players
whose top-100 pp maps are most similar to the target's. Useful as "who should
I look at to decide what to play next".

Similarity = cosine over pp-weighted song vectors (each user's top-100 maps,
weighted by their pp on the map), plus common-map count.

Usage: similar.py <player_id | player_name> [topN]
"""
import json
import math
import os
import sys
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
    vecs, songs = {}, {}
    with open(SCORES_FILE) as f:
        for line in f:
            rec = json.loads(line)
            v = {}
            for i, s in enumerate(rec["scores"]):  # scores are pp-desc sorted
                v[s["lb_id"]] = s["pp"] * (WEIGHT_DECAY ** i)
                songs[s["lb_id"]] = (s["song"], s["author"], s["stars"])
            vecs[rec["_player"]] = v
    return players, vecs, songs


def cosine(a, b):
    common = a.keys() & b.keys()
    if not common:
        return 0.0, 0
    dot = sum(a[k] * b[k] for k in common)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb), len(common)


def main():
    query = sys.argv[1]
    top_n = int(sys.argv[2]) if len(sys.argv) > 2 else 15

    players, vecs, songs = load()

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

    print(f"\nTarget: #{target['rank']} {target['name']} ({target['country']}) "
          f"{target['pp']:.0f}pp — comparing against higher-pp players\n")

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
              f"{p['name']} ({p['country']})  "
              f"https://scoresaber.com/u/{p['id']}")

    if out:
        # what the most similar higher player has that the target hasn't played
        sim, nc, p = out[0]
        pv = vecs[p["id"]]
        gaps = sorted((pp for lb, pp in pv.items() if lb not in tv),
                      reverse=True)
        new_maps = [(lb, pv[lb]) for lb in pv if lb not in tv]
        new_maps.sort(key=lambda x: -x[1])
        print(f"\n{p['name']}이(가) 플레이했지만 타깃은 안 한 상위 pp 맵:")
        for lb, pp in new_maps[:8]:
            song, author, stars = songs[lb]
            print(f"  {pp:6.1f}pp  {stars:5.2f}* {song} ({author})  "
                  f"https://scoresaber.com/leaderboard/{lb}")


if __name__ == "__main__":
    main()
