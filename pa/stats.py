"""PILOT-05 cell size statistics. Emits only pa-stats/1 keys (names owned by pa/schema.py)."""
import json
import pathlib
import re
import statistics
import sys

import yaml

from pa import schema

MB = 1024 * 1024  # "MB" in pa-stats/1 means MiB
_LOT = re.compile(r"world_(\d+)_(\d+)\.lotpack")


def cell_stats(map_dir):
    """{(cx, cy): bytes} summing lotpack + lotheader + chunkdata; a cell exists if its lotpack does."""
    root, out = pathlib.Path(map_dir), {}
    for p in root.glob("world_*_*.lotpack"):
        m = _LOT.fullmatch(p.name)
        if not m:
            continue
        cx, cy = m.groups()
        total = 0
        for f in (p, root / f"{cx}_{cy}.lotheader", root / f"chunkdata_{cx}_{cy}.bin"):
            try:
                total += f.stat().st_size
            except OSError:
                pass  # missing or unreadable companion counts as zero
        out[(int(cx), int(cy))] = total
    return out


def _med(v):
    return statistics.median(v) / MB if v else 0.0


def build_stats(map_dir, cell_size, threshold):
    cells = cell_stats(map_dir)
    pop = [b for b in cells.values() if b >= threshold]
    emp = [b for b in cells.values() if b < threshold]
    return {
        "schema": schema.STATS_ID, "cell_size": cell_size, "cell_count": len(cells),
        "populated_count": len(pop), "empty_count": len(emp), "empty_threshold_bytes": threshold,
        "mb_per_populated_cell": _med(pop),
        "mb_per_populated_cell_mean": sum(pop) / len(pop) / MB if pop else 0.0,
        "mb_per_empty_cell": _med(emp), "export_mb_total": sum(cells.values()) / MB,
        "per_cell": [{"cx": cx, "cy": cy, "mb": b / MB} for (cx, cy), b in sorted(cells.items())],
    }


def _run(args):
    cfg = yaml.safe_load(pathlib.Path(args.config).read_text(encoding="utf-8")) or {}
    thr = args.empty_threshold_bytes if args.empty_threshold_bytes is not None else cfg.get("empty_threshold_bytes")
    if type(thr) is not int or thr < 0 or type(cfg.get("cell_size")) is not int:
        sys.exit("pa stats: need int cell_size and a recorded empty_threshold_bytes (config or --empty-threshold-bytes)")
    d = build_stats(args.map_dir, cfg["cell_size"], thr)
    text = json.dumps(d, indent=2)
    if args.json:
        pathlib.Path(args.json).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


def register(subparsers):
    p = subparsers.add_parser("stats", help="MB per cell and export size for a map dir (pa-stats/1)")
    p.add_argument("map_dir")
    p.add_argument("--json", help="write JSON here instead of stdout")
    p.add_argument("--config", default="config/world.yaml")
    p.add_argument("--empty-threshold-bytes", type=int, help="overrides config empty_threshold_bytes")
    p.set_defaults(func=_run)
