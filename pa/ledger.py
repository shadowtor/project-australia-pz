"""BUILD-05: licence ledger, provenance.json, in-mod attribution and the check pa release runs before promoting.
All yaml/json/toml read here is untrusted: parsed with safe loaders, validated, paths confined to the payload."""
import json
import pathlib
import re
import tomllib

import yaml

from pa import edits

LEDGER_DIR = pathlib.Path(__file__).resolve().parent.parent / "ledger"
REQUIRED_ROWS = ("osm_odbl", "worlded_cli_gpl2plus", "pz_mapping_tools_gpl2", "knoxmap_own_mit", "pz_game_assets", "knoxify")
ROW_FIELDS = ("id", "component", "licence", "handling", "source")
OSM = "OpenStreetMap contributors"
DEFAULT_TRANSFORMATIONS = ["KnoxMap render", "scale", "rotation"]  # used only when no build record is supplied
BEGIN, END = "--- Data credit (ProjectAustralia) ---", "--- end data credit ---"


def _load(path):
    return yaml.safe_load(pathlib.Path(path).read_text(encoding="utf-8"))


def check_licences(ledger_dir=LEDGER_DIR):
    try:
        data = _load(pathlib.Path(ledger_dir) / "licences.yaml")
    except (OSError, yaml.YAMLError) as e:
        return [f"licences.yaml unreadable: {e}"]
    rows = data.get("rows") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        return ["licences.yaml needs a `rows:` list"]
    out, by_id = [], {}
    for r in rows:
        if not isinstance(r, dict) or not isinstance(r.get("id"), str):
            out.append(f"licence row without a string id: {r!r}")
            continue
        by_id[r["id"]] = r
        out += [f"licence row {r['id']} missing {f}" for f in ROW_FIELDS if not (isinstance(r.get(f), str) and r[f].strip())]
    out += [f"licence row {i} missing" for i in REQUIRED_ROWS if i not in by_id]
    k = by_id.get("knoxify")
    if k and (k.get("status") != "not_copied" or "licence unpublished" not in str(k.get("note", ""))):
        out.append("licence row knoxify must have status not_copied and note 'not copied, licence unpublished'")
    return out


def check_assets(ledger_dir=LEDGER_DIR):
    try:
        data = _load(pathlib.Path(ledger_dir) / "assets.yaml")
    except (OSError, yaml.YAMLError) as e:
        return [f"assets.yaml unreadable: {e}"]
    assets = data.get("assets") if isinstance(data, dict) else None
    if not isinstance(assets, list):
        return ["assets.yaml needs an `assets:` list"]
    out = []
    for a in assets:
        if not isinstance(a, dict):
            out.append(f"asset entry not a mapping: {a!r}")
            continue
        p, lic, src = a.get("path"), a.get("licence"), a.get("source")
        if not (isinstance(p, str) and p and not pathlib.PurePath(p).is_absolute() and ".." not in pathlib.PurePath(p).parts):
            out.append(f"asset path {p!r} must be relative with no '..'")
        if not (isinstance(lic, str) and lic.strip()) or lic.strip().lower() in ("unknown", "unlicensed", "tbd"):
            out.append(f"asset {p!r}: licence missing or unknown")
        if not (isinstance(src, str) and src.strip()):
            out.append(f"asset {p!r}: source missing")
    return out


def _files(payload, name):
    return [f for f in sorted(pathlib.Path(payload).rglob(name)) if f.is_file()]


def _read(f, payload):
    return edits.inside(f, payload).read_text(encoding="utf-8")


def check_payload(payload):
    """Problems (empty list = ok): ATTRIBUTION.txt with OSM credit, extract and transformations; every map.info credits OSM."""
    payload = pathlib.Path(payload)
    out = []
    att = _files(payload, "ATTRIBUTION.txt")
    if not att:
        out.append("payload has no ATTRIBUTION.txt")
    for f in att:
        try:
            t = _read(f, payload)
        except (ValueError, OSError, UnicodeDecodeError) as e:
            out.append(f"{f.name} unreadable or outside payload: {e}")
            continue
        for need, rx in ((OSM, re.escape(OSM)), ("Extract: <name> and a date", r"Extract:\s*\S+.*\d{4}-\d{2}-\d{2}"),
                         ("Transformations: <list>", r"Transformations:\s*\S")):
            if not re.search(rx, t):
                out.append(f"ATTRIBUTION.txt lacks {need}")
    infos = _files(payload, "map.info")
    if not infos:
        out.append("payload has no map.info")
    for f in infos:
        try:
            t = _read(f, payload)
        except (ValueError, OSError, UnicodeDecodeError) as e:
            out.append(f"map.info unreadable or outside payload: {e}")
            continue
        if not any(ln.startswith("description=") and OSM in ln for ln in t.splitlines()):
            out.append(f"{f.relative_to(payload).as_posix()} description lacks '{OSM}'")
    return out


def check_all(payload=None, ledger_dir=LEDGER_DIR):
    return check_licences(ledger_dir) + check_assets(ledger_dir) + (check_payload(payload) if payload else [])


def gate(payload):
    """Hook for pa release: licence ledger plus payload attribution."""
    return check_all(payload)


def attribution_block(extract, date, transformations):
    return "\n".join([BEGIN,
                      f"Map data © {OSM}, available under the Open Database Licence (ODbL 1.0): https://www.openstreetmap.org/copyright",
                      f"Extract: {extract} (Geofabrik, {date})",
                      "Transformations: " + ", ".join(transformations),
                      END, ""])


def description_credit(date):
    return f" Map data © {OSM} (ODbL 1.0), extract {date}."


def _pins_info(pins_path):
    p = tomllib.loads(pathlib.Path(pins_path).read_text(encoding="utf-8"))
    name = pathlib.PurePath(p["external"]["osm_pbf"]["path"]).name
    m = re.fullmatch(r"([a-z0-9-]+-(\d{2})(\d{2})(\d{2}))\.osm\.pbf", name)
    if not m:
        raise ValueError(f"cannot read extract name/date from {name!r}")
    extract = {"name": m[1], "date": f"20{m[2]}-{m[3]}-{m[4]}", "sha256": p["external"]["osm_pbf"].get("sha256")}
    tools = {"knoxmap": p["knoxmap"]["tag"], "pz_mapping_tools": p["tools"]["active"]["version"], "game": p["game"]["version"]}
    return extract, tools


def _transformations(record):
    if record is None:
        return list(DEFAULT_TRANSFORMATIONS), "default"
    t = json.loads(pathlib.Path(record).read_text(encoding="utf-8")).get("transformations")
    if not (isinstance(t, list) and t and all(isinstance(x, str) and re.fullmatch(r"[\x20-\x7e]+", x) and x.strip() for x in t)):
        raise ValueError("build record `transformations` must be a non-empty list of printable ASCII strings")
    return t, "build-record"


def attribute(payload, pins_path, build_record=None):
    """Write provenance.json, the credit block in ATTRIBUTION.txt and the credit on every map.info description. Idempotent."""
    payload = pathlib.Path(payload)
    extract, tools = _pins_info(pins_path)
    trans, src = _transformations(build_record)
    infos = _files(payload, "map.info")
    if not infos:
        raise ValueError("payload has no map.info")
    for f in infos:  # append to the last description line, keep existing text
        lines = _read(f, payload).splitlines(keepends=True)
        idx = [i for i, ln in enumerate(lines) if ln.startswith("description=")]
        if idx and OSM in lines[idx[-1]]:
            continue
        if idx:
            ln = lines[idx[-1]]
            body = ln.rstrip("\r\n")
            lines[idx[-1]] = body + description_credit(extract["date"]) + ln[len(body):]
        else:
            if lines and not lines[-1].endswith(("\n", "\r")):
                lines[-1] += "\n"
            lines.append("description=" + description_credit(extract["date"]).strip() + "\n")
        f.write_text("".join(lines), encoding="utf-8", newline="")
    block = attribution_block(extract["name"], extract["date"], trans)
    att = payload / "ATTRIBUTION.txt"
    old = _read(att, payload) if att.is_file() else ""
    if BEGIN in old and END in old:
        head, _, rest = old.partition(BEGIN)
        old = head + rest.partition(END)[2].lstrip("\n")
    att.write_text(old.rstrip("\n") + ("\n\n" if old.strip() else "") + block, encoding="utf-8", newline="")
    prov = {"extract": extract, "tools": tools, "transformations": trans, "transformations_source": src}
    (payload / "provenance.json").write_text(json.dumps(prov, indent=1) + "\n", encoding="utf-8")


def _cmd_check(a):
    problems = check_all(a.payload, a.ledger_dir)
    for p in problems:
        print("LEDGER FAIL", p)
    if not problems:
        print("LEDGER OK")
    return 1 if problems else 0


def _cmd_attribute(a):
    try:
        attribute(a.payload, a.pins, a.build_record)
    except (ValueError, OSError, KeyError, json.JSONDecodeError, tomllib.TOMLDecodeError) as e:
        print(f"LEDGER FAIL attribute: {e}")
        return 1
    print("ATTRIBUTED", a.payload)
    return 0


def register(subparsers):
    p = subparsers.add_parser("ledger", help="licence ledger, provenance and attribution")
    s = p.add_subparsers(dest="ledger_cmd", required=True)
    c = s.add_parser("check")
    c.add_argument("--payload")
    c.add_argument("--ledger-dir", default=str(LEDGER_DIR))
    c.set_defaults(func=_cmd_check)
    t = s.add_parser("attribute")
    t.add_argument("--payload", required=True)
    t.add_argument("--pins", default="PINS.toml")
    t.add_argument("--build-record")
    t.set_defaults(func=_cmd_attribute)
