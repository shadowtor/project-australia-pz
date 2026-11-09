"""BUILD-05: licence ledger, provenance, in-mod attribution, enforced by pa release."""
import json
import pathlib
import shutil
import subprocess
import sys
import unicodedata

import pytest
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pa import ledger, release  # noqa: E402

FIX = ROOT / "tests" / "fixtures" / "release" / "payload"
LEDGER = ROOT / "ledger"


def pa(*args):
    return subprocess.run([sys.executable, "-m", "pa", *args], cwd=ROOT, capture_output=True, text=True)


def bare_payload(tmp_path, attribution=True, map_info="title=T\ndescription=A map.\n"):
    p = tmp_path / "payload"
    (p / "maps" / "T").mkdir(parents=True)
    (p / "maps" / "T" / "map.info").write_text(map_info, encoding="utf-8")
    if attribution:
        (p / "ATTRIBUTION.txt").write_text("Made with KnoxMap.\n", encoding="utf-8")
    return p


def test_licences_complete():
    assert ledger.check_licences(LEDGER) == []
    rows = {r["id"]: r for r in yaml.safe_load((LEDGER / "licences.yaml").read_text(encoding="utf-8"))["rows"]}
    assert rows["knoxify"]["status"] == "not_copied" and "licence unpublished" in rows["knoxify"]["note"]


def test_missing_row_fails(tmp_path):
    d = tmp_path / "l"
    shutil.copytree(LEDGER, d)
    data = yaml.safe_load((d / "licences.yaml").read_text(encoding="utf-8"))
    data["rows"] = [r for r in data["rows"] if r["id"] != "osm_odbl"]
    (d / "licences.yaml").write_text(yaml.safe_dump(data), encoding="utf-8")
    assert any("osm_odbl" in p for p in ledger.check_licences(d))
    assert pa("ledger", "check", "--ledger-dir", str(d)).returncode != 0
    assert pa("ledger", "check").returncode == 0


def test_knoxify_must_stay_not_copied(tmp_path):
    d = tmp_path / "l"
    shutil.copytree(LEDGER, d)
    data = yaml.safe_load((d / "licences.yaml").read_text(encoding="utf-8"))
    for r in data["rows"]:
        if r["id"] == "knoxify":
            r["status"] = "copied"
    (d / "licences.yaml").write_text(yaml.safe_dump(data), encoding="utf-8")
    assert any("knoxify" in p for p in ledger.check_licences(d))


def test_payload_missing_attribution_or_credit_fails(tmp_path):
    p = bare_payload(tmp_path, attribution=False)
    assert any("ATTRIBUTION.txt" in x for x in ledger.check_payload(p))
    assert pa("ledger", "check", "--payload", str(p)).returncode != 0
    p2 = bare_payload(tmp_path / "b")
    problems = ledger.check_payload(p2)
    assert any("OpenStreetMap contributors" in x for x in problems)
    assert any("Extract" in x for x in problems) and any("Transformations" in x for x in problems)


def attribute(p, tmp_path, *extra):
    return pa("ledger", "attribute", "--payload", str(p), "--pins", str(ROOT / "PINS.toml"), *extra)


def test_attribute_writes_provenance_and_description(tmp_path):
    p = bare_payload(tmp_path)
    r = attribute(p, tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    prov = json.loads((p / "provenance.json").read_text(encoding="utf-8"))
    assert prov["extract"]["name"] == "australia-261108" and prov["extract"]["date"] == "2026-11-08"
    assert prov["tools"]["knoxmap"] == "1.8.5.5" and prov["tools"]["pz_mapping_tools"]
    assert prov["transformations"]
    info = (p / "maps" / "T" / "map.info").read_text(encoding="utf-8")
    assert info.startswith("title=T\ndescription=A map.") and "OpenStreetMap contributors" in info
    assert ledger.check_payload(p) == []
    once = (info, (p / "ATTRIBUTION.txt").read_text(encoding="utf-8"))
    assert "Made with KnoxMap." in once[1]
    attribute(p, tmp_path)  # idempotent
    assert ((p / "maps" / "T" / "map.info").read_text(encoding="utf-8"), (p / "ATTRIBUTION.txt").read_text(encoding="utf-8")) == once


def test_transformations_come_from_build_record(tmp_path):
    p = bare_payload(tmp_path)
    rec = tmp_path / "build-record.json"
    rec.write_text(json.dumps({"transformations": ["alpha step", "beta step"]}), encoding="utf-8")
    assert attribute(p, tmp_path, "--build-record", str(rec)).returncode == 0
    assert json.loads((p / "provenance.json").read_text(encoding="utf-8"))["transformations"] == ["alpha step", "beta step"]
    assert "alpha step, beta step" in (p / "ATTRIBUTION.txt").read_text(encoding="utf-8")
    rec.write_text(json.dumps({"transformations": "nope"}), encoding="utf-8")
    assert attribute(bare_payload(tmp_path / "x"), tmp_path, "--build-record", str(rec)).returncode != 0


def test_wording_has_no_hidden_characters():
    text = ledger.attribution_block("australia-261108", "2026-11-08", ["render", "scale"]) + ledger.description_credit("2026-11-08")
    for ch in text:
        assert ch in "\n" or ch == "\u00a9" or (32 <= ord(ch) < 127), repr(ch)
        assert unicodedata.category(ch) not in ("Cf", "Zs") or ch == " "


def test_assets_need_licence_and_source(tmp_path):
    d = tmp_path / "l"
    shutil.copytree(LEDGER, d)
    assert ledger.check_assets(d) == []
    for bad in ({"path": "a.png", "licence": "unknown", "source": "x"}, {"path": "a.png", "licence": "MIT"},
                {"path": "../a.png", "licence": "MIT", "source": "x"}):
        (d / "assets.yaml").write_text(yaml.safe_dump({"assets": [bad]}), encoding="utf-8")
        assert ledger.check_assets(d), bad
    (d / "assets.yaml").write_text(yaml.safe_dump({"assets": [{"path": "a.png", "licence": "CC0-1.0", "source": "https://x"}]}), encoding="utf-8")
    assert ledger.check_assets(d) == []


def test_release_enforces_ledger(tmp_path):
    root = tmp_path / "r"
    good = tmp_path / "good"
    shutil.copytree(FIX, good)
    assert pa("release", "--payload", str(good), "--version", "v2", "--root", str(root)).returncode == 0
    before = (root / "current.txt").read_bytes()
    bad = bare_payload(tmp_path / "bad", attribution=False)
    r = pa("release", "--payload", str(bad), "--version", "v3", "--root", str(root))
    assert r.returncode != 0
    assert (root / "current.txt").read_bytes() == before
    assert not (root / "releases" / "v3").exists() and (root / "staging-failed" / "v3").is_dir()
    shutil.rmtree(root / "staging-failed")
    ok = bare_payload(tmp_path / "ok")
    assert attribute(ok, tmp_path).returncode == 0
    assert pa("release", "--payload", str(ok), "--version", "v3", "--root", str(root)).returncode == 0
    assert (root / "current.txt").read_text().strip() == "v3"


def test_release_fails_when_ledger_module_broken(monkeypatch, tmp_path):
    import builtins
    real = builtins.__import__

    def fake(name, *a, **k):
        if name == "pa.ledger":
            raise ModuleNotFoundError("no", name="pa.ledger")
        return real(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", fake)
    with pytest.raises(release.ReleaseError):
        release._ledger_gate(tmp_path)
