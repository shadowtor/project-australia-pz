"""Anchor resolution, orphan reasons, report format, --strict exit code."""
import json
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from pa import edits  # noqa: E402

SQ = [(0, 0), (1, 0), (0, 1), (1, 1)]
H = edits.footprint_hash(SQ)


def edit(tile=(0, 0, 5, 5), tol=2, ref="b1", h=H):
    return {"edit_id": "e1", "kind": "feature", "_file": "features/e1.yaml", "payload": {"char": "X"},
            "anchor": {"type": "footprint", "ref": ref, "geom_hash": h, "tile": list(tile), "tolerance_tiles": tol}}


def feat(tile, ref="b1", h=H):
    return {"id": "f", "ref": ref, "geom_hash": h, "tile": list(tile)}


def test_exact_hash_anywhere_survives_and_tolerance():
    assert edits.resolve(edit(), [feat((0, 0, 5, 5))])[:3] == ("survived", None, 0)
    # translated footprint hashes equal (relative to own min corner)
    assert edits.footprint_hash([(x + 9, y + 3) for x, y in SQ]) == H
    st, reason, dist, _ = edits.resolve(edit(), [feat((0, 0, 7, 5), ref="other")])  # ref differs, hash anchors
    assert (st, reason, dist) == ("moved", None, 2)


def test_reason_codes():
    assert edits.resolve(edit(), [feat((0, 0, 5, 5), h="sha256:zz")])[:2] == ("orphan", "hash_mismatch")
    assert edits.resolve(edit(), [])[:2] == ("orphan", "missing_source")
    assert edits.resolve(edit(), [feat((0, 0, 9, 5))])[:2] == ("orphan", "moved_beyond_tolerance")


def test_index_ref_alone_never_anchors():
    st, reason, *_ = edits.resolve(edit(), [feat((0, 0, 5, 5), ref="b1", h="sha256:other")])
    assert st == "orphan"


def test_report_and_strict(tmp_path, capsys):
    rows = [edits.orphan_row(edit(), "missing_source")]
    line = edits.report(rows, (3, 1, 1), tmp_path)
    assert line == "5 edits: 3 survived, 1 moved within tolerance, 1 orphaned"
    out = capsys.readouterr().out
    assert "ORPHAN e1" in out and line in out
    got = json.loads((tmp_path / "orphans.json").read_text(encoding="utf-8"))[0]
    assert set(got) == {"edit_id", "kind", "anchor", "reason", "last_known", "file"}
    assert edits.exit_code(rows, True) == 1 and edits.exit_code(rows, False) == 0
    assert edits.exit_code([], True) == 0


def test_payload_path_traversal_rejected(tmp_path):
    d = edit()
    d["payload"] = {"path": "../evil.txt"}
    with pytest.raises(ValueError):
        edits.validate(d, tmp_path)
