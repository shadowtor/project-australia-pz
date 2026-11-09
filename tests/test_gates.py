"""BUILD-03 gates proven on deliberately broken fixtures; each failure names region and cell."""
import json
import pathlib
import re
import sys

import pytest
import yaml
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pa import cli, gates, palette  # noqa: E402

RULES = """// comment
rule
{
	label = "road"
	bitmap = 0
	color = 100 100 100   # trailing
	tiles = a b
}
rule
{
	label = "grass"
	bitmap = 0
	color = 0 200 0
	tiles = c
}
rule
{
	label = "nocolour"
	bitmap = 0
}
"""
ROAD, GRASS, BAD = (100, 100, 100), (0, 200, 0), (250, 0, 250)
CS = 4
REGIONS = {"north": [[0, 0, 0, 0]], "east": [[1, 0, 1, 0]]}
GATES_CFG = {"bmp_cell_size": CS, "road_labels": ["road"], "regions": {k: v for k, v in REGIONS.items()}}


def rules_file(tmp_path, text=RULES):
    f = tmp_path / "Rules.txt"
    f.write_text(text, encoding="utf-8")
    return f


def world_bmp(tmp_path, road_a_row=1, road_b_row=1, bad=None):
    """Two cells side by side; a road row ends at the shared edge of each."""
    img = Image.new("RGB", (CS * 2, CS), GRASS)
    for x in range(CS):
        img.putpixel((x, road_a_row), ROAD)
    for x in range(CS, CS * 2):
        img.putpixel((x, road_b_row), ROAD)
    if bad:
        img.putpixel(bad, BAD)
    f = tmp_path / "map.bmp"
    img.save(f)
    return f


def test_rules_parse(tmp_path):
    assert palette.parse_rules(rules_file(tmp_path)) == {"road": ROAD, "grass": GRASS}


def test_rules_malformed_color(tmp_path):
    with pytest.raises(ValueError, match="color"):
        palette.parse_rules(rules_file(tmp_path, 'rule\n{\n\tlabel = "x"\n\tcolor = 1 2\n}\n'))


def test_palette_gate(tmp_path, capsys):
    pal = set(palette.parse_rules(rules_file(tmp_path)).values())
    assert gates.palette_gate(world_bmp(tmp_path), pal, CS, REGIONS) == []
    f = gates.palette_gate(world_bmp(tmp_path, bad=(5, 2)), pal, CS, REGIONS)
    gates.report(f, "palette", tmp_path / "reports")
    out = capsys.readouterr().out
    assert "region=east cell=1_0 tile=5,2" in out
    assert json.loads((tmp_path / "reports" / "palette.json").read_text())[0]["region"] == "east"


def test_seam_gate(tmp_path):
    roads = {ROAD}
    assert gates.seam_gate(world_bmp(tmp_path), roads, CS, REGIONS) == []
    f = gates.seam_gate(world_bmp(tmp_path, road_b_row=2), roads, CS, REGIONS)
    assert len(f) == 1 and f[0].region == "north" and (f[0].cx, f[0].cy) == (0, 0)
    assert "1_0" in f[0].message and "east" in f[0].message


def test_bad_bmp_is_a_finding(tmp_path):
    bad = tmp_path / "x.bmp"
    bad.write_bytes(b"not a bmp")
    f = gates.palette_gate(bad, set(), CS)
    assert len(f) == 1 and "cannot read" in f[0].message


def test_cell_outside_regions_unmapped(tmp_path):
    f = gates.palette_gate(world_bmp(tmp_path, bad=(5, 2)), {ROAD, GRASS}, CS, {"north": [[0, 0, 0, 0]]})
    assert [x.region for x in f] == ["unmapped"]


def test_gates_config(tmp_path):
    good = tmp_path / "g.yaml"
    good.write_text(yaml.safe_dump(GATES_CFG), encoding="utf-8")
    assert gates.load_gates_config(good)["bmp_cell_size"] == CS
    assert gates.load_gates_config(ROOT / "config" / "gates.yaml")["road_labels"]
    for drop in ("road_labels", "bmp_cell_size", "regions"):
        bad = {k: v for k, v in GATES_CFG.items() if k != drop}
        (tmp_path / "b.yaml").write_text(yaml.safe_dump(bad), encoding="utf-8")
        with pytest.raises(ValueError, match=drop):
            gates.load_gates_config(tmp_path / "b.yaml")


def test_no_knoxify_palette():
    for f in (ROOT / "pa").glob("*.py"):
        assert "pz_colors" not in f.read_text(encoding="utf-8"), f


def routes_file(tmp_path, isolated=True):
    nodes = [{"id": i, "region": "north" if i < 2 else "east", "cell": f"{i % 2}_0"} for i in range(4)]
    edges = [[0, 1], [1, 2]] + ([] if isolated else [[2, 3]])
    f = tmp_path / "routes.yaml"
    f.write_text(yaml.safe_dump({"nodes": nodes, "edges": edges}), encoding="utf-8")
    return f


def test_connectivity(tmp_path):
    assert gates.connectivity_gate(routes_file(tmp_path, isolated=False)) == []
    f = gates.connectivity_gate(routes_file(tmp_path))
    assert len(f) == 1 and f[0].region == "east" and (f[0].cx, f[0].cy) == (1, 0)


STATS = {"schema": "pa-stats/1", "cell_size": 256, "cell_count": 4, "populated_count": 2, "empty_count": 2,
         "empty_threshold_bytes": 100, "mb_per_populated_cell": 1.0, "mb_per_empty_cell": 0.1,
         "export_mb_total": 5.0, "load_time_s": 10, "fps_driving": 40, "stream_in_ok": True,
         "per_cell": [{"cx": 0, "cy": 0, "mb": 0.5}, {"cx": 1, "cy": 0, "mb": 1.5}]}
BUDGETS = {"schema": "pa-budgets/1", "cell_size": 256, "vanilla": {}, "mb_per_populated_cell_max": 2,
           "mb_per_empty_cell_max": 1, "export_mb_total_max": 10, "cell_count_max": 10,
           "load_time_s_max": 30, "fps_driving_min": 30, "require_stream_in_ok": True}


def budget_files(tmp_path, stats=None, budgets=None):
    s, b = {**STATS, **(stats or {})}, {**BUDGETS, **(budgets or {})}
    for k in [k for k, v in {**(stats or {}), }.items() if v is None]:
        s.pop(k)
    (tmp_path / "stats.json").write_text(json.dumps(s), encoding="utf-8")
    (tmp_path / "budgets.yaml").write_text(yaml.safe_dump(b), encoding="utf-8")
    return tmp_path / "budgets.yaml", tmp_path / "stats.json"


def test_budget_pass(tmp_path):
    assert gates.budget_gate(*budget_files(tmp_path)) == []


@pytest.mark.parametrize("over", [
    {"mb_per_populated_cell": 3.0}, {"mb_per_empty_cell": 2}, {"export_mb_total": 11}, {"cell_count": 11},
    {"load_time_s": 31}, {"fps_driving": 20}, {"stream_in_ok": False}])
def test_budget_violations(tmp_path, over):
    f = gates.budget_gate(*budget_files(tmp_path, over), regions=REGIONS)
    assert len(f) == 1 and f[0].gate == "budget"
    if "mb_per_populated_cell" in over:
        assert f[0].region == "east" and (f[0].cx, f[0].cy) == (1, 0)


def test_budget_fail_closed(tmp_path):
    b, s = budget_files(tmp_path, {"mb_per_populated_cel": 1.0})  # renamed key
    assert gates.budget_gate(b, s)[0].message.startswith("schema")
    b, s = budget_files(tmp_path, budgets={"fps_min": 3})  # unknown budget key
    assert gates.budget_gate(b, s)[0].message.startswith("schema")
    b, s = budget_files(tmp_path)
    d = json.loads(s.read_text())
    del d["export_mb_total"]
    s.write_text(json.dumps(d))
    assert "schema" in gates.budget_gate(b, s)[0].message
    assert gates.budget_gate(tmp_path / "none.yaml", s)[0].gate == "budget"


def test_budget_missing_measurement_and_waive(tmp_path):
    b, s = budget_files(tmp_path, {"fps_driving": None})
    assert "not measured" in gates.budget_gate(b, s)[0].message
    b, s = budget_files(tmp_path, {"fps_driving": None}, {"waive": ["fps_driving"], "waive_reason": "no run yet"})
    assert gates.budget_gate(b, s) == []


def test_validate_cli(tmp_path, capsys):
    world = tmp_path / "world"
    world.mkdir()
    world_bmp(world, road_b_row=2, bad=(5, 2))
    routes_file(world)
    cfg = tmp_path / "gates.yaml"
    cfg.write_text(yaml.safe_dump(GATES_CFG), encoding="utf-8")
    rules = rules_file(tmp_path)
    b, s = budget_files(tmp_path, {"fps_driving": 1})
    rep = tmp_path / "reports"
    code = cli.main(["validate", "--world", str(world), "--rules", str(rules), "--gates-config", str(cfg),
                     "--budgets", str(b), "--stats", str(s), "--reports", str(rep)])
    out = capsys.readouterr().out
    assert code == 1
    for gate in ("connectivity", "seam", "palette", "budget"):
        assert re.search(rf"GATE FAIL {gate} ", out), gate
        assert (rep / f"{gate}.json").exists()
    assert "region=" in out and "cell=" in out


def test_validate_budget_only_and_clean(tmp_path, capsys):
    b, s = budget_files(tmp_path)
    assert cli.main(["validate", "--budgets", str(b), "--stats", str(s), "--reports", str(tmp_path / "r")]) == 0
    b, s = budget_files(tmp_path, {"export_mb_total": 99})
    assert cli.main(["validate", "--budgets", str(b), "--stats", str(s), "--reports", str(tmp_path / "r")]) == 1
    assert cli.main(["validate"]) == 2
