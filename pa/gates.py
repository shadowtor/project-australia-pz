"""BUILD-03 validation gates. Every gate returns Finding lists; `pa validate` prints, writes reports/<gate>.json, exits non-zero."""
import json
import pathlib
from dataclasses import asdict, dataclass

import yaml
from PIL import Image

from pa import edits, palette as palette_mod, schema

CELL = 300  # fallback BMP cell size for callers that supply none (tracer); real value is gates.yaml bmp_cell_size


@dataclass
class Finding:
    gate: str
    region: str
    cx: object
    cy: object
    tile: object
    message: str

    def line(self):
        cell = "n/a" if self.cx is None else f"{self.cx}_{self.cy}"
        tile = "n/a" if self.tile is None else f"{self.tile[0]},{self.tile[1]}"
        return f"GATE FAIL {self.gate} region={self.region} cell={cell} tile={tile}: {self.message}"


def _bare(gate, msg, region="n/a"):
    return Finding(gate, region, None, None, None, msg)


def load_palette(path):
    return {tuple(int(v) for v in ln.split()[:3]) for ln in pathlib.Path(path).read_text(encoding="utf-8").splitlines() if ln.strip()}


def load_gates_config(path):
    """gates.yaml: bmp_cell_size, road_labels, regions {name: [[x0,y0,x1,y1] inclusive cell ranges]}. Fails closed."""
    d = yaml.safe_load(pathlib.Path(path).read_text(encoding="utf-8"))
    if not isinstance(d, dict):
        raise ValueError("gates config must be a mapping")
    for k in d:
        if k not in ("bmp_cell_size", "road_labels", "regions"):
            raise ValueError(f"gates config: unknown key {k}")
    for k in ("bmp_cell_size", "road_labels", "regions"):
        if k not in d:
            raise ValueError(f"gates config: missing {k}")
    n = d["bmp_cell_size"]
    if type(n) is not int or n <= 0:
        raise ValueError("gates config: bmp_cell_size must be a positive integer")
    rl = d["road_labels"]
    if not (isinstance(rl, list) and rl and all(isinstance(x, str) for x in rl)):
        raise ValueError("gates config: road_labels must be a non-empty list of strings")
    rg = d["regions"]
    if not isinstance(rg, dict) or not rg:
        raise ValueError("gates config: regions must be a non-empty mapping")
    for name, ranges in rg.items():
        if not (isinstance(ranges, list) and ranges):
            raise ValueError(f"gates config: region {name} needs a list of ranges")
        for r in ranges:
            edits.tile_coords(r, 4)
            if len(r) != 4:
                raise ValueError(f"gates config: region {name} range {r!r} must be [x0,y0,x1,y1]")
    return d


def region_of(regions, cx, cy):
    """Region name for a cell, or 'unmapped'. regions None means one unnamed 'map' region (tracer)."""
    if regions is None:
        return "map"
    for name, ranges in regions.items():
        if any(x0 <= cx <= x1 and y0 <= cy <= y1 for x0, y0, x1, y1 in ranges):
            return name
    return "unmapped"


def road_colors(rules, labels):
    """RGB set for the road labels from parsed Rules.txt; an unknown label is an error."""
    miss = [l for l in labels if l not in rules]
    if miss:
        raise ValueError(f"road labels not in Rules.txt: {', '.join(miss)}")
    return {rules[l] for l in labels}


def _open(bmp_path, gate):
    try:
        return Image.open(bmp_path).convert("RGB"), None
    except (OSError, ValueError, Image.DecompressionBombError) as e:  # T-01-10: bad/huge BMP is a finding
        return None, _bare(gate, f"cannot read {pathlib.Path(bmp_path).name}: {e}")


def palette_gate(bmp_path, palette, cell_size=CELL, regions=None):
    """One finding per (cell, colour), at the first offending pixel."""
    img, err = _open(bmp_path, "palette")
    if err:
        return [err]
    seen, out = set(), []
    px = img.load()
    for y in range(img.height):  # ponytail: per-pixel python loop, switch to getcolors+numpy if maps get large
        for x in range(img.width):
            c = px[x, y]
            cx, cy = x // cell_size, y // cell_size
            if c not in palette and (cx, cy, c) not in seen:
                seen.add((cx, cy, c))
                out.append(Finding("palette", region_of(regions, cx, cy), cx, cy, (x, y), f"colour {c} not in palette"))
    return out


def seam_gate(bmp_path, roads, cell_size, regions=None):
    """Road/non-road must agree across every shared cell edge; one finding per adjacent cell pair."""
    img, err = _open(bmp_path, "seam")
    if err:
        return [err]
    px, out = img.load(), []
    ncx, ncy = img.width // cell_size, img.height // cell_size
    for cy in range(ncy):
        for cx in range(ncx):
            for dx, dy in ((1, 0), (0, 1)):
                ox, oy = cx + dx, cy + dy
                if ox >= ncx or oy >= ncy:
                    continue
                bad = []
                for i in range(cell_size):
                    if dx:
                        a, b = (ox * cell_size - 1, cy * cell_size + i), (ox * cell_size, cy * cell_size + i)
                    else:
                        a, b = (cx * cell_size + i, oy * cell_size - 1), (cx * cell_size + i, oy * cell_size)
                    if (px[a] in roads) != (px[b] in roads):
                        bad.append(a)
                if bad:
                    out.append(Finding("seam", region_of(regions, cx, cy), cx, cy, bad[0],
                                       f"road mismatch with cell {ox}_{oy} (region={region_of(regions, ox, oy)}) on {len(bad)} edge pixels"))
    return out


def connectivity_gate(routes_path, regions=None):
    """routes.yaml {nodes: [{id, region, cell: 'cx_cy'}], edges: [[a, b]]}; nodes outside the largest component fail."""
    try:
        d = yaml.safe_load(pathlib.Path(routes_path).read_text(encoding="utf-8"))
        if not isinstance(d, dict) or not isinstance(d.get("nodes"), list) or not isinstance(d.get("edges"), list):
            raise ValueError("needs nodes and edges lists")
        nodes = {}
        for n in d["nodes"]:
            if not isinstance(n, dict) or not isinstance(n.get("id"), (str, int)) or n["id"] in nodes:
                raise ValueError(f"bad or duplicate node {n!r}")
            cx, cy = (int(v) for v in edits.cell_id(n.get("cell")).split("_"))
            nodes[n["id"]] = (cx, cy, n.get("region") or region_of(regions, cx, cy))
        parent = {k: k for k in nodes}

        def find(k):
            while parent[k] != k:
                parent[k] = parent[parent[k]]
                k = parent[k]
            return k

        for e in d["edges"]:
            if not (isinstance(e, list) and len(e) == 2 and all(v in nodes for v in e)):
                raise ValueError(f"bad edge {e!r}")
            parent[find(e[0])] = find(e[1])
    except (OSError, ValueError, yaml.YAMLError) as e:
        return [_bare("connectivity", f"routes file invalid: {e}")]
    comps = {}
    for k in nodes:
        comps.setdefault(find(k), []).append(k)
    main = max(comps.values(), key=len, default=[])
    return [Finding("connectivity", nodes[k][2], nodes[k][0], nodes[k][1], None,
                    f"node {k} is not connected to the main network ({len(main)} nodes)")
            for c in comps.values() if c is not main for k in c]


_CEIL = ("mb_per_populated_cell", "mb_per_empty_cell", "export_mb_total", "cell_count", "load_time_s")


def budget_gate(budgets_path, stats_path, regions=None):
    """Compare a pa-stats/1 file with a pa-budgets/1 file; both read only through pa.schema (fail closed)."""
    try:
        b, s = schema.load_budgets(budgets_path), schema.load_stats(stats_path)
    except (schema.SchemaError, OSError, ValueError, yaml.YAMLError) as e:  # json errors are ValueError
        return [_bare("budget", f"schema: {e}")]
    out, waive = [], set(b.get("waive", []))
    if s["cell_size"] != b["cell_size"]:
        out.append(_bare("budget", f"cell_size mismatch: stats {s['cell_size']} vs budgets {b['cell_size']}"))
    worst = max(s.get("per_cell", []), key=lambda c: c["mb"], default=None)

    def fail(msg, k):
        if worst and k.startswith("mb_per"):
            out.append(Finding("budget", region_of(regions, worst["cx"], worst["cy"]), worst["cx"], worst["cy"], None,
                               f"{msg} (worst cell {worst['mb']} MB)"))
        else:
            out.append(_bare("budget", msg))

    for k in _CEIL + ("fps_driving", "stream_in_ok"):
        if k in waive:
            continue
        if k not in s:
            out.append(_bare("budget", f"{k} not measured and not waived"))
        elif k in _CEIL and s[k] > b[f"{k}_max"]:
            fail(f"{k} {s[k]} over ceiling {b[k + '_max']}", k)
        elif k == "fps_driving" and s[k] < b["fps_driving_min"]:
            fail(f"fps_driving {s[k]} under floor {b['fps_driving_min']}", k)
        elif k == "stream_in_ok" and b["require_stream_in_ok"] and s[k] is not True:
            fail("stream_in_ok is not true", k)
    return out


def report(findings, gate, reports_dir):
    reports_dir = pathlib.Path(reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / f"{gate}.json").write_text(json.dumps([asdict(f) for f in findings], indent=1), encoding="utf-8")
    for f in findings:
        print(f.line())


def register(subparsers):
    p = subparsers.add_parser("validate", help="run the BUILD-03 gates on whichever inputs are supplied")
    p.add_argument("--world", help="world dir holding map.bmp and routes.yaml")
    p.add_argument("--bmp")
    p.add_argument("--routes")
    p.add_argument("--rules", help="pinned tools config/Rules.txt")
    p.add_argument("--budgets")
    p.add_argument("--stats")
    p.add_argument("--gates-config", default="config/gates.yaml")
    p.add_argument("--reports", default="reports")
    p.set_defaults(func=_validate)


def _validate(a):
    bmp, routes = a.bmp, a.routes
    if a.world:
        world = pathlib.Path(a.world)
        for p in (bmp, routes):
            if p:
                edits.inside(p, world)
        if not bmp and (world / "map.bmp").exists():
            bmp = str(world / "map.bmp")
        if not routes and (world / "routes.yaml").exists():
            routes = str(world / "routes.yaml")
    if not (bmp or routes or a.budgets or a.stats):
        print("VALIDATE FAIL: no inputs supplied (--world, --bmp, --routes, --budgets/--stats)")
        return 2
    results, cfg = {}, None
    if bmp or routes:
        try:
            cfg = load_gates_config(a.gates_config)
        except (OSError, ValueError, yaml.YAMLError) as e:
            results["config"] = [_bare("config", f"gates config invalid: {e}")]
    if cfg:
        regions = cfg["regions"]
        if routes:
            results["connectivity"] = connectivity_gate(routes, regions)
        if bmp:
            try:
                if not a.rules:
                    raise ValueError("--rules is required for the palette and seam gates")
                rules = palette_mod.parse_rules(a.rules)
                size = cfg["bmp_cell_size"]
                results["palette"] = palette_gate(bmp, set(rules.values()), size, regions)
                results["seam"] = seam_gate(bmp, road_colors(rules, cfg["road_labels"]), size, regions)
            except (OSError, ValueError) as e:
                results["palette"] = [_bare("palette", str(e))]
    if a.budgets or a.stats:
        if a.budgets and a.stats:
            results["budget"] = budget_gate(a.budgets, a.stats, cfg["regions"] if cfg else None)
        else:
            results["budget"] = [_bare("budget", "--budgets and --stats must be supplied together")]
    bad = 0
    for gate, findings in results.items():
        report(findings, gate, a.reports)
        bad += len(findings)
    print(f"VALIDATE {'FAIL' if bad else 'OK'}: {', '.join(results)} ({bad} findings)")
    return 1 if bad else 0
