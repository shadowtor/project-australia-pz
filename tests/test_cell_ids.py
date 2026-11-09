import json
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from pa import compose, edits  # noqa: E402


@pytest.mark.parametrize("bad", ["../evil", "0_0/../../x", r"0_0\..", "a_b", "0_0_0", "", 0, 1.5, None])
def test_cell_id_rejects(bad):
    with pytest.raises(ValueError):
        edits.cell_id(bad)


def test_cell_id_int_hint_and_negative():
    with pytest.raises(ValueError, match="quote"):
        edits.cell_id(0)
    assert edits.cell_id("-1_2") == "-1_2"


def test_tile_coords_must_be_ints():
    assert edits.tile_coords([1, 2]) == [1, 2]
    for bad in (["a", 1], [1.5, 2], [True, 1], [1], "12", None):
        with pytest.raises(ValueError):
            edits.tile_coords(bad)


def _setup(tmp_path, locked, legacy=None):
    tmp_path.mkdir(exist_ok=True)
    gen, ed, out = tmp_path / "gen", tmp_path / "edits", tmp_path / "out"
    gen.mkdir(); (ed / "locked").mkdir(parents=True)
    (gen / "cell_0_0.txt").write_text("..\n..\n")
    (ed / "locks.yaml").write_text(f"locked: [{locked}]\n")
    (tmp_path / "x.txt").write_text("pwn")
    if legacy:
        (ed / "legacy.yaml").write_text(legacy)
    return gen, ed, out


def test_locks_traversal_fails_closed(tmp_path):
    gen, ed, out = _setup(tmp_path, "'../../x'")
    with pytest.raises(ValueError):
        compose.compose(gen, ed, out)
    assert not out.exists()


def test_unquoted_lock_int_rejected(tmp_path):
    gen, ed, out = _setup(tmp_path, "0")
    with pytest.raises(ValueError, match="quote"):
        compose.compose(gen, ed, out)


def test_legacy_edit_traversal_and_non_int_tile(tmp_path):
    bad = ("cell: '../../x'\ntile: [0, 0]\nchar: X\n", "cell: '0_0'\ntile: [a, 0]\nchar: X\n")
    for i, legacy in enumerate(bad):
        gen, ed, out = _setup(tmp_path / str(i), "'-1_2'", legacy)
        with pytest.raises(ValueError):
            compose.compose(gen, ed, out)
        assert not out.exists()


def test_valid_negative_lock_composes(tmp_path):
    gen, ed, out = _setup(tmp_path, "'-1_2'")
    (ed / "locked" / "cell_-1_2.txt").write_text("L\n")
    compose.compose(gen, ed, out)
    assert (out / "cell_-1_2.txt").read_text() == "L\n"


def test_features_json_non_int_tile(tmp_path):
    gen, ed, out = _setup(tmp_path, "'0_0'")
    (gen / "features.json").write_text(json.dumps([{"id": "f", "ref": "r", "geom_hash": "h", "tile": ["../..", 0, 0, 0]}]))
    with pytest.raises(ValueError):
        compose.compose(gen, ed, out)
