#!/usr/bin/env python3
"""Find rank-10 accuracy outliers inside 0.1-star ScoreSaber bins.

Default criterion:
  - rank-10 accuracy is in the top 10% within its star bin
  - rank-10 pp is at least 450

Accuracy is calculated as baseScore / maxScore * 100. The script reads
leaderboards.json plus map_scores.jsonl, and also map_scores_tail12.jsonl if it
exists. When the same leaderboard appears in multiple score files, the record
with more stored scores wins.
"""
import argparse
import csv
import json
import math
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
DEFAULT_DATA = HERE / "data"


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data-dir", default=DEFAULT_DATA, type=Path)
    p.add_argument("--scores", action="append",
                   help="Score JSONL file. Can be passed multiple times.")
    p.add_argument("--bin-width", type=float, default=0.1)
    p.add_argument("--top-fraction", type=float, default=0.10,
                   help="Fraction of each bin considered top accuracy.")
    p.add_argument("--pp-min", type=float, default=450.0)
    p.add_argument("--min-stars", type=float, default=None)
    p.add_argument("--max-stars", type=float, default=None,
                   help="Exclusive upper bound.")
    p.add_argument("--limit-per-bin", type=int, default=0,
                   help="Limit rows shown per bin; 0 means no limit.")
    p.add_argument("--format", choices=("markdown", "csv", "json"),
                   default="markdown")
    p.add_argument("--output", type=Path, default=None)
    return p.parse_args()


def score_files(data_dir, explicit):
    if explicit:
        return [Path(p) for p in explicit]
    candidates = [data_dir / "map_scores.jsonl",
                  data_dir / "map_scores_tail12.jsonl"]
    return [p for p in candidates if p.exists()]


def read_catalog(path):
    with path.open() as f:
        rows = json.load(f)
    return {str(r["id"]): r for r in rows}


def read_scores(paths):
    by_lb = {}
    file_stats = []
    for path in paths:
        lines = bad = used = 0
        if not path.exists():
            file_stats.append({"path": str(path), "exists": False,
                               "lines": 0, "bad": 0, "used": 0})
            continue
        with path.open() as f:
            for line in f:
                lines += 1
                try:
                    rec = json.loads(line)
                    lb = str(rec["_lb"])
                except Exception:
                    bad += 1
                    continue
                current = by_lb.get(lb)
                current_len = len(current["scores"]) if current else -1
                if len(rec.get("scores") or []) > current_len:
                    rec["_source_file"] = str(path)
                    by_lb[lb] = rec
                    used += 1
        file_stats.append({"path": str(path), "exists": True,
                           "lines": lines, "bad": bad, "used": used})
    return by_lb, file_stats


def strip_ss_markup(name):
    return re.sub(r"</?color(?:=[^>]*)?>", "", name or "")


def decimals_for(width):
    text = f"{width:.10f}".rstrip("0").rstrip(".")
    return len(text.split(".", 1)[1]) if "." in text else 0


def bin_start(stars, width):
    return math.floor((stars + 1e-9) / width) * width


def bin_label(start, width):
    places = max(1, decimals_for(width))
    return f"{start:.{places}f}-{start + width:.{places}f}"


def rank10_row(scores):
    for s in scores:
        if s.get("rank") == 10:
            return s
    return None


def build_rows(catalog, score_records, args):
    rows = []
    skipped = defaultdict(int)
    for lb, rec in score_records.items():
        meta = catalog.get(str(lb))
        if not meta:
            skipped["missing_catalog"] += 1
            continue
        stars = float(meta.get("stars") or 0)
        if args.min_stars is not None and stars < args.min_stars:
            continue
        if args.max_stars is not None and stars >= args.max_stars:
            continue
        scores = rec.get("scores") or []
        s10 = rank10_row(scores)
        if not s10:
            skipped["missing_rank10"] += 1
            continue
        max_score = meta.get("max_score") or meta.get("maxScore") or 0
        if not max_score:
            skipped["missing_max_score"] += 1
            continue
        acc = float(s10.get("base") or 0) / float(max_score) * 100
        start = bin_start(stars, args.bin_width)
        rows.append({
            "bin": bin_label(start, args.bin_width),
            "bin_start": start,
            "lb_id": str(lb),
            "song": meta.get("song"),
            "author": meta.get("author"),
            "mapper": meta.get("mapper"),
            "diff": (meta.get("diff") or "").replace("_", " ").strip(),
            "stars": stars,
            "plays": meta.get("plays"),
            "rank10_player": strip_ss_markup(s10.get("player_name")),
            "rank10_player_raw": s10.get("player_name"),
            "rank10_acc": acc,
            "rank10_pp": float(s10.get("pp") or 0),
            "rank10_modifiers": s10.get("modifiers") or "",
            "n_scores": len(scores),
            "score_source": rec.get("_source_file"),
        })
    return rows, dict(skipped)


def qualify(rows, args):
    bins = defaultdict(list)
    for row in rows:
        bins[row["bin"]].append(row)

    out_bins = []
    out_rows = []
    for label, items in sorted(bins.items(), key=lambda kv: kv[1][0]["bin_start"]):
        ordered = sorted(items, key=lambda r: r["rank10_acc"], reverse=True)
        top_count = max(1, math.ceil(len(ordered) * args.top_fraction))
        cutoff = ordered[top_count - 1]["rank10_acc"]
        qualified = [
            r for r in ordered
            if r["rank10_acc"] >= cutoff and r["rank10_pp"] >= args.pp_min
        ]
        if args.limit_per_bin > 0:
            qualified = qualified[:args.limit_per_bin]
        for r in qualified:
            r = dict(r)
            r["bin_count"] = len(items)
            r["top_count"] = top_count
            r["acc_cutoff"] = cutoff
            out_rows.append(r)
        out_bins.append({
            "bin": label,
            "bin_count": len(items),
            "top_count": top_count,
            "acc_cutoff": cutoff,
            "qualified_count": len(qualified),
        })
    return out_bins, out_rows


def render_markdown(meta, bins, rows):
    by_bin = defaultdict(list)
    for row in rows:
        by_bin[row["bin"]].append(row)

    lines = [
        "# Rank-10 Accuracy Top-Decile Maps",
        "",
        f"Generated: {meta['generated_at']}",
        f"Criterion: top {meta['top_fraction']:.1%} rank-10 accuracy within each "
        f"{meta['bin_width']} star bin, rank-10 pp >= {meta['pp_min']:.1f}",
        f"Rows considered: {meta['rows_considered']}",
        f"Qualified rows: {meta['qualified_rows']}",
        "",
        "| Bin | Maps | Top cutoff acc | Qualified |",
        "|---|---:|---:|---:|",
    ]
    for b in bins:
        lines.append(
            f"| {b['bin']} | {b['bin_count']} | {b['acc_cutoff']:.3f}% | "
            f"{b['qualified_count']} |"
        )

    for b in bins:
        items = by_bin.get(b["bin"]) or []
        if not items:
            continue
        lines.extend(["", f"## {b['bin']}"])
        for r in items:
            mods = f", mods {r['rank10_modifiers']}" if r["rank10_modifiers"] else ""
            lines.append(
                f"- {r['song']} [{r['diff']}] by {r['mapper']} "
                f"({r['stars']:.2f}*, lb {r['lb_id']}): "
                f"rank10 acc {r['rank10_acc']:.3f}%, "
                f"pp {r['rank10_pp']:.3f}, player {r['rank10_player']}{mods}"
            )
    lines.append("")
    return "\n".join(lines)


def render_csv(rows):
    fields = [
        "bin", "bin_count", "top_count", "acc_cutoff", "lb_id", "song",
        "author", "mapper", "diff", "stars", "plays", "rank10_acc",
        "rank10_pp", "rank10_player", "rank10_modifiers", "n_scores",
        "score_source",
    ]
    from io import StringIO
    buf = StringIO()
    writer = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return buf.getvalue()


def main():
    args = parse_args()
    if not (0 < args.top_fraction <= 1):
        sys.exit("--top-fraction must be in (0, 1].")
    data_dir = args.data_dir
    catalog = read_catalog(data_dir / "leaderboards.json")
    score_paths = score_files(data_dir, args.scores)
    score_records, file_stats = read_scores(score_paths)
    rows, skipped = build_rows(catalog, score_records, args)
    bins, qualified = qualify(rows, args)
    meta = {
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "data_dir": str(data_dir),
        "score_files": file_stats,
        "bin_width": args.bin_width,
        "top_fraction": args.top_fraction,
        "pp_min": args.pp_min,
        "min_stars": args.min_stars,
        "max_stars": args.max_stars,
        "catalog_rows": len(catalog),
        "score_records": len(score_records),
        "rows_considered": len(rows),
        "qualified_rows": len(qualified),
        "skipped": skipped,
    }

    if args.format == "json":
        rendered = json.dumps({"meta": meta, "bins": bins, "rows": qualified},
                              ensure_ascii=False, indent=2)
    elif args.format == "csv":
        rendered = render_csv(qualified)
    else:
        rendered = render_markdown(meta, bins, qualified)

    if args.output:
        args.output.write_text(rendered)
    else:
        print(rendered)


if __name__ == "__main__":
    main()
