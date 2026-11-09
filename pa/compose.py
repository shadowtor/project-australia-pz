import json
import pathlib
import shutil

import yaml

from pa import edits as ed


def _set(grid, x, y, ch):
    if not (0 <= y < len(grid) and 0 <= x < len(grid[y])):
        return False
    grid[y] = grid[y][:x] + ch + grid[y][x + 1:]
    return True


def _overlay(grid, text):
    """Non-space chars of an overlay/mask grid replace generated tiles. Layer data is opaque text
    (assumption A6: no Qt, so TMX tile ids are not parsed; the raw text is what gets hashed)."""
    for y, row in enumerate(text.splitlines()):
        for x, ch in enumerate(row):
            if ch != " ":
                _set(grid, x, y, ch)


def _read(p):
    return p.read_text(encoding="utf-8").splitlines()


def _write(p, grid):
    p.write_text("\n".join(grid) + "\n", encoding="utf-8")


def run(generated_dir, edits_dir, out_dir, masks_dir=None, reports_dir=None):
    """Compose with precedence generated < masks < hand edits < locked. Returns (out_dir, orphan_rows, counts)."""
    generated_dir, edits_dir, out_dir = map(pathlib.Path, (generated_dir, edits_dir, out_dir))
    reports_dir = pathlib.Path(reports_dir) if reports_dir else out_dir.parent / "reports"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    shutil.copytree(generated_dir, out_dir)
    if masks_dir:
        for m in sorted(pathlib.Path(masks_dir).glob("cell_*.txt")):
            g = _read(out_dir / m.name)
            _overlay(g, m.read_text(encoding="utf-8"))
            _write(out_dir / m.name, g)
    # legacy flat edits/*.yaml (tracer slice): cell + tile + char, applied directly
    for e in sorted(edits_dir.glob("*.yaml")):
        d = yaml.safe_load(e.read_text(encoding="utf-8"))
        if d and "cell" in d and "edit_id" not in d:
            cell = out_dir / f"cell_{d['cell']}.txt"
            g = _read(cell)
            _set(g, d["tile"][0], d["tile"][1], str(d["char"]))
            _write(cell, g)
    idx_file = generated_dir / "features.json"
    index = json.loads(idx_file.read_text(encoding="utf-8")) if idx_file.exists() else []
    rows, counts = [], [0, 0, 0]
    for e in ed.load_all(edits_dir):
        orphan = None
        if e["kind"] == "overlay":
            cell = e["anchor"]["ref"]
            src = generated_dir / f"cell_{cell}.txt"
            if not src.exists():
                orphan = "missing_source"
            elif ed.sha(src.read_bytes()) != e.get("generated_tiles_hash"):
                orphan = "hash_mismatch"  # drift check: generated tiles under the overlay changed
            else:
                g = _read(out_dir / src.name)
                _overlay(g, (edits_dir / e["payload"]["path"]).read_text(encoding="utf-8"))
                _write(out_dir / src.name, g)
                counts[0] += 1
        else:
            st, orphan, _, f = ed.resolve(e, index)
            if st != "orphan":
                cx, cy, lx, ly = f["tile"]
                cell = out_dir / f"cell_{cx}_{cy}.txt"
                ox, oy = e["payload"].get("offset", [0, 0])
                g = _read(cell) if cell.exists() else []
                if _set(g, lx + ox, ly + oy, str(e["payload"]["char"])):
                    _write(cell, g)
                    counts[0 if st == "survived" else 1] += 1
                else:
                    orphan = "missing_source"
        if orphan:
            rows.append(ed.orphan_row(e, orphan))
            counts[2] += 1
    # locked cells ignore regenerated content entirely
    for cell in ed.load_locks(edits_dir):
        locked = edits_dir / "locked" / f"cell_{cell}.txt"
        if locked.exists():
            shutil.copyfile(locked, out_dir / f"cell_{cell}.txt")
    ed.report(rows, counts, reports_dir)
    return out_dir, rows, counts


def compose(generated_dir, edits_dir, out_dir, **kw):
    return run(generated_dir, edits_dir, out_dir, **kw)[0]


def register(sub):
    p = sub.add_parser("compose", help="compose generated + masks + edits + locks")
    p.add_argument("--generated", required=True)
    p.add_argument("--edits", default="edits")
    p.add_argument("--out", required=True)
    p.add_argument("--masks")
    p.add_argument("--strict", action="store_true", help="exit non-zero if any edit is orphaned")
    p.set_defaults(func=lambda a: ed.exit_code(run(a.generated, a.edits, a.out, a.masks)[1], a.strict))
