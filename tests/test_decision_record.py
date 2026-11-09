import pytest
import yaml

from pa import cli, decision as dc


def trials(group, dirs, passes=3, fail=None):
    out, n = [], 0
    for d in dirs:
        for i in range(passes):
            n += 1
            out.append({"n": n, "group": group, "direction": d, "pass": (d, i) != fail, "note": ""})
    return out


def attempt(root, feature, name, impl="a", verdict=None, reload="pass", ts=None, cause="", shots=True, **kw):
    """Write spike/evidence/<feature>/<name>/run.yaml; defaults describe a fully passing single-group attempt."""
    d = root / feature / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "s.png").write_bytes(b"png")
    multi = feature == "ferry"
    if multi and reload == "pass":
        reload = {"foot": "pass", "vehicle": "pass"}
    if ts is None:
        ts = (trials("foot", ["round_trip"]) + trials("vehicle", ["round_trip"])) if multi else \
            trials("main", {"ramp": ["up", "down"], "basement": ["in", "out"]}[feature])
    doc = {"build": "42.22.2", "mod_version": "0.1", "date": "2026-11-10", "implementation": impl,
           "trials": ts, "reload_result": reload, "console_errors": [], "screenshots": ["s.png"] if shots else [],
           "next_step": "none", "logged_cause": cause}
    doc["verdicts" if multi else "verdict"] = verdict or ({"foot": "PROVEN", "vehicle": "PROVEN"} if multi else "PROVEN")
    doc.update(kw)
    (d / "run.yaml").write_text(yaml.safe_dump(doc))
    return d


def problems(root, feature):
    return dc.check_feature(feature, root)[0]


def test_schema_requires_fields(tmp_path):
    d = attempt(tmp_path, "ramp", "a1")
    doc = yaml.safe_load((d / "run.yaml").read_text())
    del doc["reload_result"]
    doc["bogus"] = 1
    (d / "run.yaml").write_text(yaml.safe_dump(doc))
    p = problems(tmp_path, "ramp")
    assert any("reload_result" in x for x in p) and any("unknown key bogus" in x for x in p)


def test_proven_ok_and_failed_trial_rejected(tmp_path):
    attempt(tmp_path, "ramp", "a1")
    assert problems(tmp_path, "ramp") == []
    attempt(tmp_path, "ramp", "a2", ts=trials("main", ["up", "down"], fail=("down", 1)))
    assert any("PROVEN" in x and "rejected" in x for x in problems(tmp_path, "ramp"))


def test_failed_reload_and_inconclusive_accepted(tmp_path):
    attempt(tmp_path, "ramp", "a1", reload="fail")
    assert any("PROVEN" in x for x in problems(tmp_path, "ramp"))
    attempt(tmp_path, "ramp", "a1", reload="fail", verdict="INCONCLUSIVE")
    assert problems(tmp_path, "ramp") == []


def test_proven_needs_three_per_direction(tmp_path):
    attempt(tmp_path, "basement", "a1", ts=trials("main", ["in", "out"], passes=2))
    assert any("PROVEN" in x for x in problems(tmp_path, "basement"))


def test_proven_needs_screenshot(tmp_path):
    attempt(tmp_path, "ramp", "a1", shots=False)
    assert any("screenshot" in x for x in problems(tmp_path, "ramp"))


def test_missing_screenshot_file_rejected(tmp_path):
    attempt(tmp_path, "ramp", "a1", screenshots=["nope.png"])
    assert any("nope.png" in x for x in problems(tmp_path, "ramp"))


def ro(root, impl, cause="crash", fail=("down", 0), name=None):
    return attempt(root, "ramp", name or impl, impl=impl, verdict="RULED OUT", cause=cause,
                   ts=trials("main", ["up", "down"], fail=fail), reload="pass")


def test_ruled_out_needs_two_different_implementations(tmp_path):
    ro(tmp_path, "x", name="a1")
    assert any("RULED OUT" in x for x in problems(tmp_path, "ramp"))  # only one attempt
    ro(tmp_path, "x", name="a2")
    assert any("RULED OUT" in x for x in problems(tmp_path, "ramp"))  # same implementation
    ro(tmp_path, "y", name="a2")
    assert problems(tmp_path, "ramp") == []


def test_ruled_out_needs_cause_and_same_failure(tmp_path):
    ro(tmp_path, "x", name="a1")
    ro(tmp_path, "y", cause="", name="a2")
    assert any("logged_cause" in x or "RULED OUT" in x for x in problems(tmp_path, "ramp"))
    ro(tmp_path, "y", fail=("up", 0), name="a2")  # failed a different way
    assert any("RULED OUT" in x for x in problems(tmp_path, "ramp"))


def test_ferry_mixed_rolls_up_inconclusive(tmp_path):
    ts = trials("foot", ["round_trip"]) + trials("vehicle", ["round_trip"], fail=("round_trip", 2))
    attempt(tmp_path, "ferry", "a1", ts=ts, verdict={"foot": "PROVEN", "vehicle": "INCONCLUSIVE"},
            reload={"foot": "pass", "vehicle": "fail"})
    (tmp_path / "ferry" / "verdict.md").write_text("verdict_foot: PROVEN\nverdict_vehicle: INCONCLUSIVE\n")
    p, got, roll = dc.check_feature("ferry", tmp_path)
    assert p == [] and got == {"foot": "PROVEN", "vehicle": "INCONCLUSIVE"} and roll == "INCONCLUSIVE"


def test_rollup():
    assert dc.rollup(["PROVEN", "PROVEN"]) == "PROVEN"
    assert dc.rollup(["RULED OUT", "RULED OUT"]) == "RULED OUT"
    assert dc.rollup(["PROVEN", "RULED OUT"]) == "INCONCLUSIVE"
    assert dc.rollup([]) == "INCONCLUSIVE"


def test_ferry_reload_must_be_mapping(tmp_path):
    attempt(tmp_path, "ferry", "a1", reload="fail")
    assert any("reload_result" in x for x in problems(tmp_path, "ferry"))


def test_verdict_md_overclaim_fails(tmp_path):
    attempt(tmp_path, "ramp", "a1", reload="fail", verdict="INCONCLUSIVE")
    (tmp_path / "ramp").joinpath("verdict.md").write_text("verdict_ramp: PROVEN\n")
    assert any("verdict.md" in x and "evidence supports INCONCLUSIVE" in x for x in problems(tmp_path, "ramp"))
    (tmp_path / "ramp").joinpath("verdict.md").write_text("verdict_ramp: INCONCLUSIVE\n")
    assert problems(tmp_path, "ramp") == []


def _decision(tmp_path, monkeypatch, extra=None, drop=()):
    ev = tmp_path / "spike" / "evidence"
    for f in ("ramp", "basement", "ferry"):
        attempt(ev, f, "a1")
    for f, names in {"ramp": ["ramp"], "basement": ["basement"], "ferry": ["foot", "vehicle"]}.items():
        (ev / f / "verdict.md").write_text("".join(f"verdict_{n}: PROVEN\n" for n in names))
    lines = {"cell_format": 256, "cell_count": 10, "mb_per_populated_cell": 1.2, "mb_per_empty_cell": 0.1,
             "export_mb_total": 20.5, "new_save_load_time_s": 40, "fps_driving": 55, "stream_in_ok": "true",
             "verdict_ramp": "PROVEN", "verdict_basement": "PROVEN", "verdict_ferry": "PROVEN",
             "verdict_ferry_foot": "PROVEN", "verdict_ferry_vehicle": "PROVEN", "build": "42.22.2",
             "date": "2026-11-10", "evidence_ramp": "spike/evidence/ramp",
             "evidence_basement": "spike/evidence/basement", "evidence_ferry": "spike/evidence/ferry"}
    lines.update(extra or {})
    for k in drop:
        del lines[k]
    f = tmp_path / "decision.md"
    f.write_text("# Decision\n\n" + "".join(f"{k}: {v}\n" for k, v in lines.items()))
    monkeypatch.chdir(tmp_path)
    return f, ev


def test_decision_ok_and_cli(tmp_path, monkeypatch):
    f, ev = _decision(tmp_path, monkeypatch)
    assert dc.check_decision(f, ev) == []
    assert cli.main(["decision", "check", "--decision", str(f), "--evidence", str(ev)]) == 0
    assert cli.main(["decision", "check", "--feature", "ramp", "--evidence", str(ev)]) == 0


def test_decision_wrong_rollup_and_missing(tmp_path, monkeypatch):
    f, ev = _decision(tmp_path, monkeypatch, {"verdict_ferry": "INCONCLUSIVE"}, drop=("fps_driving",))
    p = dc.check_decision(f, ev)
    assert any("verdict_ferry" in x for x in p) and any("missing fps_driving" in x for x in p)
    assert cli.main(["decision", "check", "--decision", str(f), "--evidence", str(ev)]) == 1


def test_decision_waiver_and_bad_values(tmp_path, monkeypatch):
    f, ev = _decision(tmp_path, monkeypatch, {"waived": "[fps_driving]"}, drop=("fps_driving",))
    assert any("waive_reason" in x for x in dc.check_decision(f, ev))
    f, ev = _decision(tmp_path, monkeypatch, {"waived": "[fps_driving]", "waive_reason": "no overlay"}, drop=("fps_driving",))
    assert dc.check_decision(f, ev) == []
    f, ev = _decision(tmp_path, monkeypatch, {"cell_format": 128, "evidence_ramp": "../x"})
    p = dc.check_decision(f, ev)
    assert any("cell_format" in x for x in p) and any("evidence_ramp" in x for x in p)


def test_decision_verdict_md_mismatch(tmp_path, monkeypatch):
    f, ev = _decision(tmp_path, monkeypatch)
    (ev / "ramp" / "verdict.md").write_text("verdict_ramp: INCONCLUSIVE\n")
    assert any("verdict.md" in x for x in dc.check_decision(f, ev))
