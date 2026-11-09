"""End-to-end proof of the thin pipeline slice (pins, generate stand-in, compose, gate, release)."""
import hashlib
import importlib
import pathlib
import re
import sys

import pytest
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pa import cli  # noqa: E402

GOOD = (10, 20, 30)
BAD = (250, 0, 250)


def make_fixture(root, bad_pixel=False):
    (root / "generated").mkdir(parents=True)
    (root / "edits").mkdir()
    gen = root / "generated" / "cell_0_0.txt"
    gen.write_text("....\n....\n", encoding="utf-8")
    digest = hashlib.sha256(gen.read_bytes()).hexdigest()
    (root / "PINS.toml").write_text(f'[files]\n"generated/cell_0_0.txt" = "{digest}"\n', encoding="utf-8")
    (root / "edits" / "e1.yaml").write_text("cell: 0_0\ntile: [1, 1]\nchar: X\n", encoding="utf-8")
    (root / "palette.txt").write_text("10 20 30\n", encoding="utf-8")
    img = Image.new("RGB", (4, 4), GOOD)
    if bad_pixel:
        img.putpixel((2, 3), BAD)
    img.save(root / "map.bmp")
    return root


def run(fixture, work, capsys):
    code = cli.main(["tracer", "--fixture", str(fixture), "--work", str(work)])
    return code, capsys.readouterr().out


def test_tracer_happy_path(tmp_path, capsys):
    fx, work = make_fixture(tmp_path / "fx"), tmp_path / "work"
    code, _ = run(fx, work, capsys)
    assert code == 0
    cell = (work / "composed" / "cell_0_0.txt").read_text(encoding="utf-8")
    assert cell.splitlines()[1] == ".X.."
    name = (work / "current.txt").read_text(encoding="utf-8").strip()
    assert (work / "releases" / name).is_dir()
    assert (work / "releases" / name / "cell_0_0.txt").read_text(encoding="utf-8") == cell


def test_pins_mismatch_fails_closed(tmp_path, capsys):
    fx, work = make_fixture(tmp_path / "fx"), tmp_path / "work"
    (fx / "generated" / "cell_0_0.txt").write_text("tampered\n", encoding="utf-8")
    code, _ = run(fx, work, capsys)
    assert code != 0
    assert not (work / "current.txt").exists()


def test_palette_gate_names_region_and_cell(tmp_path, capsys):
    fx, work = make_fixture(tmp_path / "fx", bad_pixel=True), tmp_path / "work"
    code, out = run(fx, work, capsys)
    assert code != 0
    assert re.search(r"GATE FAIL palette region=\S+ cell=0_0 tile=2,3", out)
    assert not (work / "current.txt").exists()
    assert not (work / "releases").exists() or not any((work / "releases").iterdir())


def test_autoregister_skips_missing_but_propagates_inner_import_error(monkeypatch):
    real = importlib.import_module

    def fake(name, *a, **k):
        if name == "pa.missing":
            raise ModuleNotFoundError("no pa.missing", name="pa.missing")
        if name == "pa.broken":
            raise ModuleNotFoundError("no requests", name="requests")
        return real(name, *a, **k)

    monkeypatch.setattr(cli.importlib, "import_module", fake)
    cli.register_all(None, names=("missing",))  # skipped silently
    with pytest.raises(ModuleNotFoundError):
        cli.register_all(None, names=("broken",))


def test_no_unsafe_yaml_load():
    for f in (ROOT / "pa").glob("*.py"):
        assert not re.search(r"yaml\.load\(", f.read_text(encoding="utf-8")), f
