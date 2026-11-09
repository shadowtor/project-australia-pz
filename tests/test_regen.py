"""D-15 regeneration test. Overlay layers are treated as opaque text hashed raw (assumption A6, no Qt/TMX parsing)."""
import hashlib
import json
import pathlib
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from pa import cli, compose, edits  # noqa: E402

SQ = [(0, 0), (1, 0), (0, 1), (1, 1)]
TRI = [(0, 0), (2, 0), (0, 2)]


def gen_fixture(gen, remove=None, shift=None):
    """Fixture generator, run twice so regeneration is genuine. Perturbation changes only the feature index."""
    gen.mkdir(parents=True)
    for c in ("0_0", "1_0", "2_0"):
        (gen / f"cell_{c}.txt").write_text("........\n" * 8, encoding="utf-8")
    feats = [
        {"id": "w1", "ref": "b1", "geom_hash": edits.footprint_hash(SQ), "tile": [0, 0, 2, 2]},
        {"id": "w2", "ref": "b2", "geom_hash": edits.footprint_hash(TRI), "tile": [1, 0, 4, 4]},
    ]
    if remove:
        feats = [f for f in feats if f["id"] != remove]
    if shift:
        for f in feats:
            if f["id"] == shift:
                f["tile"][2] += 6  # past tolerance 2
    (gen / "features.json").write_text(json.dumps(feats), encoding="utf-8")
    return gen


def promote_all(ed_dir, gen):
    edits.promote(ed_dir, gen, "sign1", "feature",
                  {"type": "footprint", "ref": "b1", "geom_hash": edits.footprint_hash(SQ), "tile": [0, 0, 2, 2], "tolerance_tiles": 2},
                  {"char": "A", "offset": [1, 0]})
    edits.promote(ed_dir, gen, "sign2", "feature",
                  {"type": "footprint", "ref": "b2", "geom_hash": edits.footprint_hash(TRI), "tile": [1, 0, 4, 4], "tolerance_tiles": 2},
                  {"char": "B"})
    edits.promote(ed_dir, gen, "paint", "overlay", {"ref": "2_0"}, {}, overlay_text="  Z\n", cell="2_0")


def snap(d):
    return {p.relative_to(d).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(d.rglob("*")) if p.is_file()}


def cells(d):
    return {p.name: p.read_bytes() for p in d.glob("cell_*.txt")}


def test_edits_survive_regeneration(tmp_path):
    ed_dir = tmp_path / "edits"
    gen = gen_fixture(tmp_path / "generated")
    promote_all(ed_dir, gen)
    before = snap(ed_dir)
    shutil.rmtree(gen)
    gen = gen_fixture(tmp_path / "generated")
    _, rows, counts = compose.run(gen, ed_dir, tmp_path / "composed")
    assert rows == [] and counts == [3, 0, 0]
    assert snap(ed_dir) == before
    assert (tmp_path / "composed" / "cell_0_0.txt").read_text().splitlines()[2][3] == "A"
    assert (tmp_path / "composed" / "cell_1_0.txt").read_text().splitlines()[4][4] == "B"
    assert (tmp_path / "composed" / "cell_2_0.txt").read_text().splitlines()[0][2] == "Z"


def test_perturbation_orphans_exactly_two(tmp_path):
    ed_dir = tmp_path / "edits"
    gen = gen_fixture(tmp_path / "g1")
    promote_all(ed_dir, gen)
    base, _, _ = compose.run(gen, ed_dir, tmp_path / "base")
    pert = gen_fixture(tmp_path / "g2", remove="w1", shift="w2")
    out, rows, counts = compose.run(pert, ed_dir, tmp_path / "pert")
    assert {r["edit_id"]: r["reason"] for r in rows} == {"sign1": "missing_source", "sign2": "moved_beyond_tolerance"}
    assert counts == [1, 0, 2]
    b, p = cells(base), cells(out)
    assert {n for n in b if b[n] != p[n]} == {"cell_0_0.txt", "cell_1_0.txt"}  # only the two orphaned edits' cells
    assert b["cell_2_0.txt"] == p["cell_2_0.txt"]
    assert "A" not in p["cell_0_0.txt"].decode() and "B" not in p["cell_1_0.txt"].decode()
    kept = snap(ed_dir)
    assert "features/sign1.yaml" in kept and "features/sign2.yaml" in kept  # orphans never deleted
    assert (tmp_path / "reports" / "orphans.json").exists()


def test_strict_exit_via_cli(tmp_path):
    ed_dir = tmp_path / "edits"
    gen = gen_fixture(tmp_path / "g1")
    promote_all(ed_dir, gen)
    pert = gen_fixture(tmp_path / "g2", remove="w1")
    args = ["compose", "--generated", str(pert), "--edits", str(ed_dir), "--out", str(tmp_path / "o")]
    assert cli.main(args) == 0
    assert cli.main(args + ["--strict"]) != 0
    assert cli.main(["compose", "--generated", str(gen), "--edits", str(ed_dir), "--out", str(tmp_path / "o2"), "--strict"]) == 0


def test_precedence_mask_overlay_lock(tmp_path):
    ed_dir = tmp_path / "edits"
    gen = gen_fixture(tmp_path / "g")
    masks = tmp_path / "masks"
    masks.mkdir()
    (masks / "cell_2_0.txt").write_text("MMM\n", encoding="utf-8")  # mask over generated
    promote_all(ed_dir, gen)  # overlay puts Z at col 2 over the mask
    (ed_dir / "locked").mkdir()
    (ed_dir / "locked" / "cell_0_0.txt").write_text("LOCKED\n", encoding="utf-8")
    (ed_dir / "locks.yaml").write_text("locked: ['0_0']\n", encoding="utf-8")
    out, _, _ = compose.run(gen, ed_dir, tmp_path / "c", masks_dir=masks)
    assert (out / "cell_2_0.txt").read_text().splitlines()[0][:3] == "MMZ"
    assert (out / "cell_0_0.txt").read_text() == "LOCKED\n"
    # a regenerated (different) cell 0_0 is still ignored in favour of the lock
    (gen / "cell_0_0.txt").write_text("xxxxxxxx\n", encoding="utf-8")
    out, _, _ = compose.run(gen, ed_dir, tmp_path / "c")
    assert (out / "cell_0_0.txt").read_text() == "LOCKED\n"


def test_overlay_drift_reports_hash_mismatch(tmp_path):
    ed_dir = tmp_path / "edits"
    gen = gen_fixture(tmp_path / "g")
    promote_all(ed_dir, gen)
    (gen / "cell_2_0.txt").write_text("changed!\n", encoding="utf-8")
    out, rows, _ = compose.run(gen, ed_dir, tmp_path / "c")
    assert [(r["edit_id"], r["reason"]) for r in rows] == [("paint", "hash_mismatch")]
    assert "Z" not in (out / "cell_2_0.txt").read_text()


def test_promote_is_sole_writer(tmp_path):
    import re
    for f in pathlib.Path(__file__).resolve().parent.parent.glob("pa/*.py"):
        src = f.read_text(encoding="utf-8")
        if f.name != "edits.py":
            assert not re.search(r"edits_dir\s*/[^\n]*\.(write_text|write_bytes)|copyfile\(.*edits", src), f
