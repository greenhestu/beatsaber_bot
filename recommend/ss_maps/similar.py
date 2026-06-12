#!/usr/bin/env python3
"""Find ranked maps whose leaderboard player-ordering resembles a target map.

Each map is its top-240 leaderboard: an ordered list of players.
Similarity between two maps over their common players:
  - spearman : rank correlation of the common players' relative order,
               shrunk by overlap size (n/(n+25)) so thin overlap can't win.
  - rbo      : rank-biased overlap (p=0.97) of the two full ordered lists —
               top-weighted "same people in the same upper region" measure.
  - resid    : Pearson correlation of skill-adjusted percentiles (each
               player's within-map percentile minus their mean across maps) —
               isolates "who OVER/UNDERperforms here" once global skill is
               removed; this is the discriminating signal when raw orderings
               all agree because good players top everything.

Final ranking: 0.5*spearman_shrunk + 0.5*resid_shrunk (rbo shown for context).

Usage: similar.py <leaderboard_id> [topN]
"""
import json
import math
import os
import sqlite3
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = "ss"
PFX = "" if SRC == "ss" else "bl_"
CATALOG_FILE = os.path.join(HERE, "data", f"{PFX}leaderboards.json")
SCORES_FILE = os.path.join(HERE, "data", f"{PFX}map_scores.jsonl")
DB_FILE = os.path.join(HERE, "data", f"{PFX}topology.db")
MIN_COMMON = 20
SHRINK = 25


def build_db():
    meta = {l["id"]: l for l in json.load(open(CATALOG_FILE))}
    con = sqlite3.connect(DB_FILE)
    con.execute("DROP TABLE IF EXISTS scores")
    con.execute("DROP TABLE IF EXISTS maps")
    con.execute("""CREATE TABLE scores (
        lb_id INT, player_id TEXT, player_name TEXT, country TEXT,
        pos INT, rank INT, mod_score INT, pp REAL, acc REAL,
        modifiers TEXT, full_combo INT)""")
    con.execute("""CREATE TABLE maps (
        lb_id INT PRIMARY KEY, song TEXT, author TEXT, mapper TEXT,
        diff TEXT, stars REAL, max_pp REAL, plays INT, n_scores INT)""")
    n = 0
    with open(SCORES_FILE) as f:
        for line in f:
            rec = json.loads(line)
            lb = rec["_lb"]
            m = meta.get(lb)
            if not m:
                continue
            rows = []
            for i, s in enumerate(rec["scores"]):
                acc = s.get("acc")
                if acc is None:
                    acc = s["mod"] / m["max_score"] * 100 if m["max_score"] else None
                rows.append((lb, s["player_id"], s["player_name"], s["country"],
                             i, s["rank"], s["mod"], s["pp"], acc,
                             s["modifiers"], 1 if s.get("fc") else 0))
            con.executemany("INSERT INTO scores VALUES (?,?,?,?,?,?,?,?,?,?,?)", rows)
            con.execute("INSERT OR REPLACE INTO maps VALUES (?,?,?,?,?,?,?,?,?)",
                        (lb, m["song"], m["author"], m["mapper"], m["diff"],
                         m["stars"], m["max_pp"], m["plays"], len(rows)))
            n += len(rows)
    con.execute("CREATE INDEX idx_lb ON scores(lb_id)")
    con.execute("CREATE INDEX idx_pl ON scores(player_id)")
    con.commit()
    nm = con.execute("SELECT COUNT(*) FROM maps").fetchone()[0]
    print(f"topology.db: {n} scores across {nm} maps")
    return con


def load(con):
    """lb -> ordered player list (by leaderboard rank), and lb -> {player: pos}."""
    order = defaultdict(list)
    for lb, pid in con.execute(
            "SELECT lb_id, player_id FROM scores ORDER BY lb_id, pos"):
        order[lb].append(pid)
    meta = {r[0]: r[1:] for r in con.execute(
        "SELECT lb_id, song, author, mapper, diff, stars, max_pp, n_scores FROM maps")}
    return dict(order), meta


def spearman_common(pos_a, pos_b, common):
    """Spearman over common players' relative orders within each map."""
    ra = {p: i for i, p in enumerate(sorted(common, key=lambda p: pos_a[p]))}
    rb = {p: i for i, p in enumerate(sorted(common, key=lambda p: pos_b[p]))}
    n = len(common)
    if n < 2:
        return 0.0
    d2 = sum((ra[p] - rb[p]) ** 2 for p in common)
    return 1 - 6 * d2 / (n * (n * n - 1))


def rbo(list_a, list_b, p=0.97):
    """Rank-biased overlap (extrapolated, truncated lists)."""
    seen_a, seen_b = set(), set()
    overlap = 0
    s = 0.0
    depth = min(len(list_a), len(list_b))
    for d in range(depth):
        a, b = list_a[d], list_b[d]
        if a == b:
            overlap += 1
        else:
            if a in seen_b:
                overlap += 1
            if b in seen_a:
                overlap += 1
            seen_a.add(a)
            seen_b.add(b)
        s += (overlap / (d + 1)) * (p ** d)
    return (1 - p) * s


def pearson(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    sx = math.sqrt(sum((a - mx) ** 2 for a in xs))
    sy = math.sqrt(sum((b - my) ** 2 for b in ys))
    return sxy / (sx * sy) if sx > 0 and sy > 0 else 0.0


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    target = args[0]
    try:
        target = int(target)
    except ValueError:
        pass  # BeatLeader ids are strings
    top_n = int(args[1]) if len(args) > 1 else 25

    if not os.path.exists(DB_FILE) or "--rebuild" in sys.argv:
        con = build_db()
    else:
        con = sqlite3.connect(DB_FILE)

    order, meta = load(con)
    if target not in order:
        sys.exit(f"leaderboard {target} not in db ({len(order)} maps)")

    pos = {lb: {p: i for i, p in enumerate(lst)} for lb, lst in order.items()}

    # skill-adjusted percentile residuals
    pct = {}
    for lb, lst in order.items():
        n = len(lst)
        if n >= 2:
            pct[lb] = {p: 1 - i / (n - 1) for i, p in enumerate(lst)}
    sums, cnts = defaultdict(float), defaultdict(int)
    for d in pct.values():
        for p, v in d.items():
            sums[p] += v
            cnts[p] += 1
    pmean = {p: sums[p] / cnts[p] for p in sums}
    resid = {lb: {p: v - pmean[p] for p, v in d.items()} for lb, d in pct.items()}

    t_pos, t_list, t_res = pos[target], order[target], resid[target]
    out = []
    for lb, lst in order.items():
        if lb == target:
            continue
        common = t_pos.keys() & pos[lb].keys()
        nc = len(common)
        if nc < MIN_COMMON:
            continue
        sp = spearman_common(t_pos, pos[lb], common) * nc / (nc + SHRINK)
        cl = sorted(common)
        rs = pearson([t_res[p] for p in cl],
                     [resid[lb][p] for p in cl]) * nc / (nc + SHRINK)
        score = 0.5 * sp + 0.5 * rs
        out.append((score, sp, rs, rbo(t_list, lst), nc, lb))
    out.sort(reverse=True)

    def url(lb):
        if SRC == "bl":
            return f"https://beatleader.com/leaderboard/global/{lb}/1"
        return f"https://scoresaber.com/leaderboard/{lb}"

    def fmt(lb):
        song, author, mapper, diff, stars, maxpp, ns = meta[lb]
        d = diff.replace("_", " ").replace("SoloStandard", "").strip()
        return f"{stars:5.2f}* {song} ({author}) [{d}] by {mapper}"

    print(f"\nTarget: {fmt(target)}  "
          f"{url(target)}\n")
    print(f"{'score':>6} {'spear':>6} {'resid':>6} {'rbo':>5} {'n':>4}  map")
    for score, sp, rs, rb_, nc, lb in out[:top_n]:
        print(f"{score:6.3f} {sp:6.3f} {rs:6.3f} {rb_:5.3f} {nc:4d}  {fmt(lb)}  "
              f"{url(lb)}")


if __name__ == "__main__":
    main()
