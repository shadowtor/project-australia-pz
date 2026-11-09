import json
import pathlib
from dataclasses import asdict, dataclass

from PIL import Image

CELL = 300  # PZ cell size in tiles


@dataclass
class Finding:
    gate: str
    region: str
    cx: int
    cy: int
    tile: tuple
    message: str

    def line(self):
        return (f"GATE FAIL {self.gate} region={self.region} cell={self.cx}_{self.cy} "
                f"tile={self.tile[0]},{self.tile[1]}: {self.message}")


def load_palette(path):
    return {tuple(int(v) for v in ln.split()[:3]) for ln in pathlib.Path(path).read_text(encoding="utf-8").splitlines() if ln.strip()}


def palette_gate(bmp_path, palette, region="map"):
    """One finding per (cell, colour), at the first offending pixel."""
    img = Image.open(bmp_path).convert("RGB")
    seen, out = set(), []
    px = img.load()
    for y in range(img.height):  # ponytail: per-pixel python loop, switch to getcolors+numpy if maps get large
        for x in range(img.width):
            c = px[x, y]
            key = (x // CELL, y // CELL, c)
            if c not in palette and key not in seen:
                seen.add(key)
                out.append(Finding("palette", region, x // CELL, y // CELL, (x, y), f"colour {c} not in palette"))
    return out


def report(findings, gate, reports_dir):
    reports_dir = pathlib.Path(reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / f"{gate}.json").write_text(json.dumps([asdict(f) for f in findings], indent=1), encoding="utf-8")
    for f in findings:
        print(f.line())
