"""Hybrid edit-safe model (D-12..D-15): anchors, resolution, orphan report, promote (sole writer of edits/)."""
import hashlib
import json
import pathlib

import yaml

# D-12 anchor schema lives here, one place (costly to change: every edit and the composer reference it).
SCHEMA = {
    "edit_id": "str, unique",
    "kind": ("feature", "overlay", "lock"),
    "anchor": {
        "type": ("footprint", "osm_way", "osm_node", "cell_tile"),
        "ref": "str; generator index ref. UNSTABLE across rebuilds, never anchors alone",
        "geom_hash": "sha256:<hex> of footprint tile coords relative to own min corner (the real anchor)",
        "tile": "[cx, cy, lx, ly] last-known 256-cell and local tile",
        "tolerance_tiles": "int, max move that still counts as the same feature",
    },
    "payload": "feature: {char, offset:[ox,oy]}; overlay: {path: file inside edits/}",
    "generated_tiles_hash": "sha256:<hex> of the generated cell overlaid (set by promote, D-13)",
}
CELL = 256
REASONS = ("missing_source", "moved_beyond_tolerance", "hash_mismatch")


def sha(data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    return "sha256:" + hashlib.sha256(data).hexdigest()


def footprint_hash(tiles):
    """Hash of tile coords [(x, y)...] relative to the polygon's own min corner (translation invariant)."""
    mx, my = min(x for x, _ in tiles), min(y for _, y in tiles)
    rel = sorted((x - mx, y - my) for x, y in tiles)
    return sha(json.dumps(rel))


def _glob(tile):
    cx, cy, lx, ly = tile
    return cx * CELL + lx, cy * CELL + ly


def validate(d, edits_dir=None):
    """Explicit schema checks; raises ValueError. yaml.safe_load is the only parser used (T-01-08)."""
    if not isinstance(d, dict) or not d.get("edit_id"):
        raise ValueError("edit needs edit_id")
    if d.get("kind") not in SCHEMA["kind"]:
        raise ValueError(f"{d['edit_id']}: bad kind")
    a = d.get("anchor")
    if not isinstance(a, dict) or a.get("type") not in SCHEMA["anchor"]["type"]:
        raise ValueError(f"{d['edit_id']}: bad anchor type")
    if a["type"] != "cell_tile":
        if not a.get("geom_hash") or not (isinstance(a.get("tile"), list) and len(a["tile"]) == 4):
            raise ValueError(f"{d['edit_id']}: anchor needs geom_hash and 4-item tile")
    if not isinstance(a.get("ref"), str):
        raise ValueError(f"{d['edit_id']}: anchor.ref must be a string (quote cell ids like '0_0')")
    p = d.get("payload")
    if not isinstance(p, dict):
        raise ValueError(f"{d['edit_id']}: payload must be a mapping")
    if "path" in p:
        if edits_dir is None:
            raise ValueError("payload path needs edits_dir to check")
        root = pathlib.Path(edits_dir).resolve()
        target = (root / p["path"]).resolve()
        if target != root and root not in target.parents:
            raise ValueError(f"{d['edit_id']}: payload path escapes edits/")
    return d


def load_all(edits_dir):
    """All feature/overlay edit records, validated, each tagged with its source file."""
    edits_dir = pathlib.Path(edits_dir)
    out = []
    for sub in ("features", "overlays"):
        for f in sorted((edits_dir / sub).glob("*.yaml")):
            d = validate(yaml.safe_load(f.read_text(encoding="utf-8")), edits_dir)
            d["_file"] = f.relative_to(edits_dir).as_posix()
            out.append(d)
    return out


def load_locks(edits_dir):
    f = pathlib.Path(edits_dir) / "locks.yaml"
    if not f.exists():
        return []
    return [str(c) for c in (yaml.safe_load(f.read_text(encoding="utf-8")) or {}).get("locked", [])]


def resolve(edit, index):
    """Resolution order per RESEARCH Pattern 2 -> (status, reason, distance, found).
    status: survived | moved | orphan. index: [{id, ref, geom_hash, tile}]."""
    a = edit["anchor"]
    exact = [f for f in index if f["geom_hash"] == a["geom_hash"]]
    if exact:
        ax, ay = _glob(a["tile"])
        f = min(exact, key=lambda f: max(abs(_glob(f["tile"])[0] - ax), abs(_glob(f["tile"])[1] - ay)))
        fx, fy = _glob(f["tile"])
        dist = max(abs(fx - ax), abs(fy - ay))
        if dist > a.get("tolerance_tiles", 0):
            return "orphan", "moved_beyond_tolerance", dist, f
        return ("survived" if dist == 0 else "moved"), None, dist, f
    if any(f["ref"] == a["ref"] for f in index):
        return "orphan", "hash_mismatch", None, None
    return "orphan", "missing_source", None, None


def orphan_row(edit, reason):
    a = edit["anchor"]
    return {"edit_id": edit["edit_id"], "kind": edit["kind"], "anchor": f"{a['type']}:{a['ref']}",
            "reason": reason, "last_known": a.get("tile") or a["ref"], "file": edit["_file"]}


def report(rows, counts, reports_dir):
    """Write orphans.json, print table + summary. counts = (survived, moved, orphaned)."""
    reports_dir = pathlib.Path(reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "orphans.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    for r in rows:
        print(f"ORPHAN {r['edit_id']:<24} {r['kind']:<8} {r['reason']:<24} {r['anchor']} {r['last_known']} {r['file']}")
    s, m, o = counts
    line = f"{s + m + o} edits: {s} survived, {m} moved within tolerance, {o} orphaned"
    print(line)
    return line


def exit_code(rows, strict):
    return 1 if strict and rows else 0


def promote(edits_dir, generated_dir, edit_id, kind, anchor, payload, overlay_text=None, cell=None):
    """The ONLY writer of edits/ (D-13). Records cell, overlaid-tile hash and anchor. overlay needs cell+overlay_text."""
    edits_dir, generated_dir = pathlib.Path(edits_dir), pathlib.Path(generated_dir)
    rec = {"edit_id": edit_id, "kind": kind, "anchor": anchor, "payload": dict(payload)}
    sub = "overlays" if kind == "overlay" else "features"
    if kind == "overlay":
        cell = str(cell)
        rec["anchor"] = {"type": "cell_tile", "ref": cell, **{k: v for k, v in anchor.items() if k != "type"}}
        rec["payload"]["path"] = f"overlays/{cell}_{edit_id}.txt"
        rec["generated_tiles_hash"] = sha((generated_dir / f"cell_{cell}.txt").read_bytes())
    validate(rec, edits_dir)
    d = edits_dir / sub
    d.mkdir(parents=True, exist_ok=True)
    if kind == "overlay":
        (edits_dir / rec["payload"]["path"]).write_text(overlay_text, encoding="utf-8")
    (d / f"{edit_id}.yaml").write_text(yaml.safe_dump(rec, sort_keys=False), encoding="utf-8")
    return rec


def register(sub):
    p = sub.add_parser("promote", help="promote a hand edit into edits/ (human-only)")
    p.add_argument("--edits", default="edits")
    p.add_argument("--generated", required=True)
    p.add_argument("--edit-id", required=True)
    p.add_argument("--kind", choices=("feature", "overlay"), required=True)
    p.add_argument("--cell", help="cell id, e.g. 0_0 (overlay)")
    p.add_argument("--layers", help="overlay file to promote (overlay)")
    p.add_argument("--anchor", required=True, help="anchor as YAML/JSON mapping")
    p.add_argument("--payload", default="{}", help="payload as YAML/JSON mapping")
    p.set_defaults(func=_promote_cli)


def _promote_cli(a):
    text = pathlib.Path(a.layers).read_text(encoding="utf-8") if a.layers else None
    promote(a.edits, a.generated, a.edit_id, a.kind, yaml.safe_load(a.anchor), yaml.safe_load(a.payload), text, a.cell)
    print(f"PROMOTED {a.edit_id}")
    return 0
