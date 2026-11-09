import json
import pathlib

import pytest
import yaml

from pa import schema
from pa.schema import SchemaError, load_budgets, load_stats

STATS = {
    "schema": "pa-stats/1", "cell_size": 256, "cell_count": 4, "populated_count": 3,
    "empty_count": 1, "empty_threshold_bytes": 1024, "mb_per_populated_cell": 1.5,
    "mb_per_empty_cell": 0.01, "export_mb_total": 5.0,
}
BUDGETS = {
    "schema": "pa-budgets/1", "cell_size": 256, "vanilla": {"mb_per_populated_cell": 2.0},
    "mb_per_populated_cell_max": 3.0, "mb_per_empty_cell_max": 0.1, "export_mb_total_max": 100.0,
    "cell_count_max": 500, "load_time_s_max": 60.0, "fps_driving_min": 30.0,
    "require_stream_in_ok": True,
}


def _json(tmp_path, d):
    p = tmp_path / "s.json"
    p.write_text(json.dumps(d), encoding="utf-8")
    return p


def _yaml(tmp_path, d):
    p = tmp_path / "b.yaml"
    p.write_text(yaml.safe_dump(d), encoding="utf-8")
    return p


def test_stats_required_keys(tmp_path):
    assert load_stats(_json(tmp_path, STATS)) == STATS
    for k in STATS:
        d = {x: v for x, v in STATS.items() if x != k}
        with pytest.raises(SchemaError, match=k):
            load_stats(_json(tmp_path, d))


def test_stats_unknown_and_wrong_type(tmp_path):
    with pytest.raises(SchemaError, match="export_size_mb"):
        load_stats(_json(tmp_path, {**STATS, "export_size_mb": 1.0}))
    with pytest.raises(SchemaError, match="cell_count"):
        load_stats(_json(tmp_path, {**STATS, "cell_count": "4"}))
    with pytest.raises(SchemaError, match="cell_count"):
        load_stats(_json(tmp_path, {**STATS, "cell_count": True}))
    with pytest.raises(SchemaError, match="schema"):
        load_stats(_json(tmp_path, {**STATS, "schema": "pa-stats/2"}))


def test_stats_optional_in_game_keys(tmp_path):
    d = {**STATS, "load_time_s": 12.0, "fps_driving": 45, "stream_in_ok": True,
         "attribution_visible": True, "machine": {"cpu": "x"}, "build": "42.22.2",
         "date": "2026-01-01", "method": "m", "label": "l", "notes": "n",
         "runs": [{"load_time_s": 11, "fps_driving": 44.5, "stream_in_ok": True, "note": "a"}],
         "per_cell": [{"cx": 0, "cy": 1, "mb": 1.2}]}
    assert load_stats(_json(tmp_path, d)) == d
    with pytest.raises(SchemaError, match="fps_driving"):
        load_stats(_json(tmp_path, {**STATS, "runs": [{"load_time_s": 1}]}))
    with pytest.raises(SchemaError, match="load_time_s"):
        load_stats(_json(tmp_path, {**STATS, "runs": [{"load_time_s": "x", "fps_driving": 1}]}))
    with pytest.raises(SchemaError, match="mb"):
        load_stats(_json(tmp_path, {**STATS, "per_cell": [{"cx": 0, "cy": 0}]}))


def test_budgets(tmp_path):
    assert load_budgets(_yaml(tmp_path, BUDGETS)) == BUDGETS
    for k in BUDGETS:
        d = {x: v for x, v in BUDGETS.items() if x != k}
        with pytest.raises(SchemaError, match=k):
            load_budgets(_yaml(tmp_path, d))
    with pytest.raises(SchemaError, match="bogus"):
        load_budgets(_yaml(tmp_path, {**BUDGETS, "bogus": 1}))
    ok = {**BUDGETS, "waive": ["fps_driving"], "waive_reason": "no vehicle in pilot"}
    assert load_budgets(_yaml(tmp_path, ok)) == ok
    with pytest.raises(SchemaError, match="waive_reason"):
        load_budgets(_yaml(tmp_path, {**BUDGETS, "waive": ["fps_driving"]}))
    with pytest.raises(SchemaError, match="nope"):
        load_budgets(_yaml(tmp_path, {**ok, "waive": ["nope"]}))


def test_safe_loading_and_non_mapping(tmp_path):
    assert "yaml.load(" not in pathlib.Path(schema.__file__).read_text(encoding="utf-8")
    with pytest.raises(SchemaError):
        load_stats(_json(tmp_path, [1, 2]))
    p = tmp_path / "x.yaml"
    p.write_text("- 1\n- 2\n", encoding="utf-8")
    with pytest.raises(SchemaError):
        load_budgets(p)
