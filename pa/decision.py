"""D-02/D-04 evidence checker: run.yaml per attempt, verdict.md per feature, decision.md. yaml.safe_load only.

pa/decision.py is the only place that spells the verdict.md line format and the rollup.
"""
import datetime
import itertools
import pathlib
import re
import sys

import yaml

from pa import edits

PROVEN, RULED_OUT, INCONCLUSIVE = "PROVEN", "RULED OUT", "INCONCLUSIVE"
VERDICTS = (PROVEN, RULED_OUT, INCONCLUSIVE)
GROUPS = {"ramp": ("main",), "basement": ("main",), "ferry": ("foot", "vehicle")}  # the one constant
# D-03 required trial directions per group; PROVEN needs >=3 passes in each (D-01). Extra directions
# (park, reload_inside, drive_off...) may be logged but must pass too.
REQUIRED_DIRS = {("ramp", "main"): ("up", "down"), ("basement", "main"): ("in", "out"),
                 ("ferry", "foot"): ("round_trip",), ("ferry", "vehicle"): ("round_trip",)}
PASSES_NEEDED = 3
RELOAD = ("pass", "fail", "not_run")
DECISION_VALUES = {"cell_format": (256, 300), "cell_count": int, "mb_per_populated_cell": float,
                   "mb_per_empty_cell": float, "export_mb_total": float, "new_save_load_time_s": float,
                   "fps_driving": float, "stream_in_ok": bool}
WAIVABLE = tuple(k for k in DECISION_VALUES if k != "cell_format")
_TOP = {"build": str, "mod_version": str, "date": (str, datetime.date), "implementation": str,
        "trials": list, "console_errors": list, "screenshots": list, "next_step": str}
_TRIAL = {"n": int, "group": str, "direction": str, "pass": bool, "note": str}
_LINE = re.compile(r"^([a-z][a-z0-9_]*):[ \t]*(.*?)\s*$")


def vname(feature, group):
    """Name used in verdict_<name> lines: the feature for single-group features, else the group."""
    return feature if group == "main" else group


def rollup(verdicts):
    """D-02 feature rollup: all PROVEN -> PROVEN, all RULED OUT -> RULED OUT, anything else INCONCLUSIVE."""
    vs = list(verdicts)
    if vs and all(v == PROVEN for v in vs):
        return PROVEN
    if vs and all(v == RULED_OUT for v in vs):
        return RULED_OUT
    return INCONCLUSIVE


def _ok(v, t):
    if t is int:
        return type(v) is int
    if t is float:
        return isinstance(v, (int, float)) and not isinstance(v, bool)
    return isinstance(v, t) and (t is not str or v.strip() != "")


def _val_ok(k, v):
    t = DECISION_VALUES[k]
    return (type(v) is int and v in t) if isinstance(t, tuple) else _ok(v, t)


def _group_state(att, g):
    ts, rel = att["trials"].get(g, []), att["reload"].get(g)
    bad_dirs = {t["direction"] for t in ts if not t["pass"]}
    proven = bool(ts) and not bad_dirs and rel == "pass"
    for d in REQUIRED_DIRS[(att["feature"], g)]:
        proven = proven and sum(1 for t in ts if t["direction"] == d) >= PASSES_NEEDED
    return {"proven": proven, "failed": bool(bad_dirs) or rel == "fail",
            "sig": (tuple(sorted(bad_dirs)), rel == "fail")}  # "failed the same way" = same sig


def _ruled_out(atts, g):
    cand = []
    for a in atts:
        st = _group_state(a, g)
        if st["failed"] and a["logged_cause"].strip():
            cand.append((a["impl"], st["sig"]))
    return any(x[0] != y[0] and x[1] == y[1] for x, y in itertools.combinations(cand, 2))


def group_verdict(atts, g):
    """Best verdict the evidence supports for one group (D-02)."""
    if any(_group_state(a, g)["proven"] for a in atts):
        return PROVEN
    return RULED_OUT if _ruled_out(atts, g) else INCONCLUSIVE


def load_attempt(path, feature, problems):
    """Parse and schema-check one run.yaml; returns a normalised attempt dict or None."""
    path = pathlib.Path(path)
    tag = f"{path.parent.name}/run.yaml"

    def bad(msg):
        problems.append(f"{tag}: {msg}")

    try:
        d = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as e:
        bad(f"unreadable: {e}")
        return None
    groups = GROUPS[feature]
    multi = len(groups) > 1
    if not isinstance(d, dict):
        bad("expected a mapping")
        return None
    vkey = "verdicts" if multi else "verdict"
    n0 = len(problems)
    for k in d:
        if k not in set(_TOP) | {"reload_result", "logged_cause", vkey}:
            bad(f"unknown key {k}")
    for k, t in _TOP.items():
        if k not in d:
            bad(f"missing {k}")
        elif not _ok(d[k], t):
            bad(f"wrong type or empty: {k} (quote versions and dates)")
    if not isinstance(d.get("logged_cause", ""), str):
        bad("logged_cause must be a string")
    rr = d.get("reload_result")
    if multi:
        reload = rr if isinstance(rr, dict) and set(rr) == set(groups) and all(v in RELOAD for v in rr.values()) else None
    else:
        reload = {"main": rr} if rr in RELOAD else None
    if reload is None:
        bad(f"reload_result must be one of {RELOAD}" + (" per group" if multi else ""))
    claimed = d.get(vkey)
    claimed = claimed if multi else {"main": claimed}
    if not (isinstance(claimed, dict) and set(claimed) == set(groups) and all(v in VERDICTS for v in claimed.values())):
        bad(f"{vkey} missing or not drawn from {VERDICTS}" + (f" for groups {groups}" if multi else ""))
    trials = {g: [] for g in groups}
    for i, t in enumerate(d["trials"] if isinstance(d.get("trials"), list) else []):
        if not isinstance(t, dict) or any(k not in _TRIAL for k in t) or not all(k in t for k in ("n", "direction", "pass")):
            bad(f"trials[{i}] needs n, direction, pass (optional group, note)")
            continue
        t = {"group": "main", **t}
        if not all(_ok(t[k], _TRIAL[k]) for k in t if k != "note") or not isinstance(t.get("note", ""), str) or t["group"] not in groups:
            bad(f"trials[{i}] has a bad value or group (groups: {groups})")
            continue
        trials[t["group"]].append(t)
    shots = d["screenshots"] if isinstance(d.get("screenshots"), list) else []
    for s in shots:
        try:
            ok = isinstance(s, str) and edits.inside(path.parent / s, path.parent).is_file()
        except (ValueError, OSError):
            ok = False
        if not ok:
            bad(f"screenshot {s!r} is not a file inside the attempt dir")
    if len(problems) > n0:
        return None
    return {"dir": path.parent.name, "feature": feature, "impl": d["implementation"],
            "logged_cause": d.get("logged_cause") or "", "trials": trials, "reload": reload,
            "claimed": claimed, "has_shots": bool(shots)}


def _claim_problems(att, atts, problems):
    for g, c in att["claimed"].items():
        if c == INCONCLUSIVE:
            continue
        st, name = _group_state(att, g), vname(att["feature"], g)
        if not att["has_shots"]:
            problems.append(f"{att['dir']}: {c} for {name} needs at least one screenshot (D-04)")
        if c == PROVEN and not st["proven"]:
            problems.append(f"{att['dir']}: PROVEN for {name} rejected: needs >={PASSES_NEEDED} passes per required "
                            f"direction {REQUIRED_DIRS[(att['feature'], g)]}, no failed trial and reload_result pass (D-01, D-02)")
        if c == RULED_OUT:
            if not st["failed"] or not att["logged_cause"].strip():
                problems.append(f"{att['dir']}: RULED OUT for {name} needs a failed trial/reload and a non-empty logged_cause (D-02)")
            elif not _ruled_out(atts, g):
                problems.append(f"{att['dir']}: RULED OUT for {name} needs two attempts with different implementation "
                                "that failed the same way, both with a logged_cause (D-02)")


def read_lines(path):
    """verdict.md/decision.md style `key: value` lines -> ({key: yaml-parsed value}, {key: raw}, duplicate keys)."""
    vals, raw, dup = {}, {}, []
    for ln in pathlib.Path(path).read_text(encoding="utf-8").splitlines():
        m = _LINE.match(ln)
        if not m:
            continue
        k, v = m.groups()
        if k in raw:
            dup.append(k)
        raw[k] = v
        try:
            vals[k] = yaml.safe_load(v) if v else None
        except yaml.YAMLError:
            vals[k] = v
    return vals, raw, dup


def check_feature(feature, evidence):
    """Returns (problems, {verdict name: verdict}, feature rollup verdict)."""
    if feature not in GROUPS:
        return [f"unknown feature {feature!r}; expected one of {sorted(GROUPS)}"], {}, INCONCLUSIVE
    problems = []
    fdir = pathlib.Path(evidence) / feature
    runs = sorted(fdir.glob("*/run.yaml")) if fdir.is_dir() else []
    if not runs:
        return [f"{feature}: no spike evidence runs under {fdir}"], {}, INCONCLUSIVE
    atts = [a for a in (load_attempt(p, feature, problems) for p in runs) if a]
    for a in atts:
        _claim_problems(a, atts, problems)
    got = {vname(feature, g): group_verdict(atts, g) for g in GROUPS[feature]}
    if (fdir / "verdict.md").is_file():
        _, raw, dup = read_lines(fdir / "verdict.md")
        problems += [f"verdict.md: duplicate line {k}" for k in dup if k.startswith("verdict_")]
        for name, v in got.items():
            claim = raw.get(f"verdict_{name}")
            if claim not in VERDICTS:
                problems.append(f"verdict.md: missing or invalid verdict_{name} (use one of {VERDICTS})")
            elif claim != INCONCLUSIVE and claim != v:
                problems.append(f"verdict.md: verdict_{name}: {claim} but evidence supports {v} (D-02)")
    return problems, got, rollup(got.values())


def check_decision(decision, evidence):
    problems = []
    try:
        vals, raw, dup = read_lines(decision)
    except OSError as e:
        return [f"decision unreadable: {e}"]
    problems += [f"decision.md: duplicate line {k}" for k in dup]
    waived = vals.get("waived") or []
    if not (isinstance(waived, list) and all(w in WAIVABLE for w in waived)):
        problems.append(f"decision.md: waived must be a list drawn from {WAIVABLE}")
        waived = []
    if waived and not str(vals.get("waive_reason") or "").strip():
        problems.append("decision.md: waived needs a non-empty waive_reason")
    for k in DECISION_VALUES:
        if k not in vals:
            if k not in waived:
                problems.append(f"decision.md: missing {k} (or waive it with waived + waive_reason)")
        elif not _val_ok(k, vals[k]):
            problems.append(f"decision.md: bad value for {k}: {raw[k]!r}")
    for k in ("build", "date"):
        if not raw.get(k):
            problems.append(f"decision.md: missing {k}")
    for feature, groups in GROUPS.items():
        fp, got, roll = check_feature(feature, evidence)
        problems += [f"{feature}: {p}" for p in fp]
        link = raw.get(f"evidence_{feature}")
        try:
            link_ok = bool(link) and edits.inside(link, evidence).is_dir()
        except (ValueError, OSError):
            link_ok = False
        if not link_ok:
            problems.append(f"decision.md: evidence_{feature} must link an existing dir inside {evidence}")
        vf = pathlib.Path(evidence) / feature / "verdict.md"
        vraw = read_lines(vf)[1] if vf.is_file() else {}
        for name, v in {**got, **({feature: roll} if len(groups) > 1 else {})}.items():
            key = f"verdict_{feature}_{name}" if name in got and name != feature else f"verdict_{name}"
            if raw.get(key) != v:
                problems.append(f"decision.md: {key}: {raw.get(key)!r} but recomputed {v}")
            if name in got and vraw.get(f"verdict_{name}") != raw.get(key):
                problems.append(f"decision.md: {key} does not match {feature}/verdict.md")
    return problems


def _run(args):
    if not (args.feature or args.decision):
        sys.exit("pa decision check: give --feature and/or --decision")
    problems = []
    if args.feature:
        fp, got, roll = check_feature(args.feature, args.evidence)
        problems += fp
        if not fp:
            print(f"{args.feature}: " + ", ".join(f"{k}={v}" for k, v in got.items()) + f" -> {roll}")
    if args.decision:
        problems += check_decision(args.decision, args.evidence)
    for p in problems:
        print(f"DECISION FAIL {p}")
    return 1 if problems else 0


def register(subparsers):
    p = subparsers.add_parser("decision", help="check spike evidence and decision.md (D-02, D-04)")
    sub = p.add_subparsers(dest="decision_cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("--feature", choices=sorted(GROUPS))
    c.add_argument("--decision")
    c.add_argument("--evidence", default="spike/evidence")
    c.set_defaults(func=_run)
