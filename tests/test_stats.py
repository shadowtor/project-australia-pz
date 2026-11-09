import json

import pytest
import yaml

from pa import cli, schema, stats

MB = 1024 * 1024


def _mk(d, cx, cy, lotpack, header=10, chunk=20):
    (d / f"world_{cx}_{cy}.lotpack").write_bytes(b"x" * lotpack)
    (d / f"{cx}_{cy}.lotheader").write_bytes(b"x" * header)
    (d / f"chunkdata_{cx}_{cy}.bin").write_bytes(b"x" * chunk)


@pytest.fixture
def mapdir(tmp_path):
    d = tmp_path / "map"
    d.mkdir()
    _mk(d, 0, 0, 5000)
    _mk(d, 0, 1, 7000)
    _mk(d, 1, 0, 100)
    (d / "notes.txt").write_bytes(b"zzzz")
    (d / "world_a_b.lotpack").write_bytes(b"zzzz")
    (d / "world_1_1.lotpack.bak").write_bytes(b"zzzz")
    return d


def test_cell_sizes_include_all_three_files(mapdir):
    s = stats.cell_stats(mapdir)
    assert s == {(0, 0): 5030, (0, 1): 7030, (1, 0): 130}  # bad names ignored (test 4)


def test_threshold_splits_empty(mapdir):
    d = stats.build_stats(mapdir, 256, 1000)
    assert (d["cell_count"], d["populated_count"], d["empty_count"]) == (3, 2, 1)
    assert d["empty_threshold_bytes"] == 1000
    assert d["mb_per_populated_cell"] == pytest.approx(6030 / MB)  # median of 5030, 7030
    assert d["mb_per_empty_cell"] == pytest.approx(130 / MB)
    assert d["export_mb_total"] == pytest.approx(12190 / MB)


def test_cli_json_passes_schema(mapdir, tmp_path, monkeypatch):
    cfg = tmp_path / "world.yaml"
    cfg.write_text(yaml.safe_dump({"cell_size": 300, "empty_threshold_bytes": 1000}))
    out = tmp_path / "out.json"
    assert cli.main(["stats", str(mapdir), "--json", str(out), "--config", str(cfg)]) == 0
    d = schema.load_stats(out)
    assert d["cell_size"] == 300 and d["schema"] == "pa-stats/1"
    assert {"cx": 0, "cy": 1, "mb": pytest.approx(7030 / MB)} in d["per_cell"]
    assert "mb_per_populated_cell_mean" in d


def test_threshold_must_be_recorded(mapdir, tmp_path):
    cfg = tmp_path / "world.yaml"
    cfg.write_text(yaml.safe_dump({"cell_size": 256}))
    with pytest.raises(SystemExit):
        cli.main(["stats", str(mapdir), "--config", str(cfg)])
