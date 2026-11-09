import pathlib
import shutil

import yaml


def compose(generated_dir, edits_dir, out_dir):
    """Copy generated cells to out_dir, then apply hand edits (precedence: generated < edit)."""
    generated_dir, edits_dir, out_dir = map(pathlib.Path, (generated_dir, edits_dir, out_dir))
    if out_dir.exists():
        shutil.rmtree(out_dir)
    shutil.copytree(generated_dir, out_dir)
    for e in sorted(edits_dir.glob("*.yaml")):
        d = yaml.safe_load(e.read_text(encoding="utf-8"))
        cell = out_dir / f"cell_{d['cell']}.txt"
        x, y = d["tile"]
        rows = cell.read_text(encoding="utf-8").splitlines()
        rows[y] = rows[y][:x] + str(d["char"]) + rows[y][x + 1:]
        cell.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return out_dir
