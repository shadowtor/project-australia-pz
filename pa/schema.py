"""Single owner of the pa-stats/1 and pa-budgets/1 key names (fail closed)."""
import json

import yaml

STATS_ID, BUDGETS_ID = "pa-stats/1", "pa-budgets/1"
_INT, _NUM, _BOOL, _STR, _MAP, _LIST = "int", "num", "bool", "str", "map", "list"

# key -> (type, required)
STATS_KEYS = {
    "schema": (_STR, True), "cell_size": (_INT, True), "cell_count": (_INT, True),
    "populated_count": (_INT, True), "empty_count": (_INT, True),
    "empty_threshold_bytes": (_INT, True), "mb_per_populated_cell": (_NUM, True),
    "mb_per_empty_cell": (_NUM, True), "export_mb_total": (_NUM, True),
    "per_cell": (_LIST, False), "mb_per_populated_cell_mean": (_NUM, False),
    "load_time_s": (_NUM, False), "fps_driving": (_NUM, False), "stream_in_ok": (_BOOL, False),
    "attribution_visible": (_BOOL, False), "runs": (_LIST, False), "machine": (_MAP, False),
    "build": (_STR, False), "date": (_STR, False), "method": (_STR, False),
    "label": (_STR, False), "notes": (_STR, False),
}
BUDGET_KEYS = {
    "schema": (_STR, True), "cell_size": (_INT, True), "vanilla": (_MAP, True),
    "mb_per_populated_cell_max": (_NUM, True), "mb_per_empty_cell_max": (_NUM, True),
    "export_mb_total_max": (_NUM, True), "cell_count_max": (_NUM, True),
    "load_time_s_max": (_NUM, True), "fps_driving_min": (_NUM, True),
    "require_stream_in_ok": (_BOOL, True),
    "waive": (_LIST, False), "waive_reason": (_STR, False),
    "build": (_STR, False), "date": (_STR, False),
}
WAIVABLE = ("mb_per_populated_cell", "mb_per_empty_cell", "export_mb_total", "cell_count",
            "load_time_s", "fps_driving", "stream_in_ok")
_RUN_KEYS = {"load_time_s": (_NUM, True), "fps_driving": (_NUM, True),
             "stream_in_ok": (_BOOL, False), "note": (_STR, False)}
_CELL_KEYS = {"cx": (_INT, True), "cy": (_INT, True), "mb": (_NUM, True)}


class SchemaError(ValueError):
    pass


def _typed(v, t):
    if t == _BOOL:
        return isinstance(v, bool)
    if t == _INT:
        return isinstance(v, int) and not isinstance(v, bool)
    if t == _NUM:
        return isinstance(v, (int, float)) and not isinstance(v, bool)
    return isinstance(v, {_STR: str, _MAP: dict, _LIST: list}[t])


def _check(d, spec, where=""):
    if not isinstance(d, dict):
        raise SchemaError(f"{where or 'document'}: expected a mapping")
    for k in d:
        if k not in spec:
            raise SchemaError(f"{where}unknown key: {k}")
    for k, (t, req) in spec.items():
        if k not in d:
            if req:
                raise SchemaError(f"{where}missing required key: {k}")
        elif not _typed(d[k], t):
            raise SchemaError(f"{where}wrong type for key {k}: expected {t}")


def load_stats(path):
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    _check(d, STATS_KEYS)
    if d["schema"] != STATS_ID:
        raise SchemaError(f"key schema must be {STATS_ID}")
    for i, r in enumerate(d.get("runs", [])):
        _check(r, _RUN_KEYS, f"runs[{i}]: ")
    for i, c in enumerate(d.get("per_cell", [])):
        _check(c, _CELL_KEYS, f"per_cell[{i}]: ")
    return d


def load_budgets(path):
    with open(path, encoding="utf-8") as f:
        d = yaml.safe_load(f)
    _check(d, BUDGET_KEYS)
    if d["schema"] != BUDGETS_ID:
        raise SchemaError(f"key schema must be {BUDGETS_ID}")
    w = d.get("waive", [])
    for x in w:
        if x not in WAIVABLE:
            raise SchemaError(f"key waive: {x} is not a measurable key")
    if w and not d.get("waive_reason"):
        raise SchemaError("key waive_reason is required when waive is non-empty")
    return d
