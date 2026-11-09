"""BUILD-01: offline KnoxMap wrapper, exercised against a fake KnoxMap (no network, no real tools)."""
import json
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pa import build  # noqa: E402

FAKE = ROOT / "tests" / "fixtures" / "fake_knoxmap"

CFG = """map_name: fakemap
mod_id: fakemod
mod_name: Fake Mod
bbox: {south: -37.8, west: 144.97, north: -37.797, east: 144.974}
meters_per_tile: 1
standalone: true
cells: [[0, 0, 0, 0]]
settings: {landcover: "off"}
"""


@pytest.fixture
def env(tmp_path, monkeypatch):
    pins = tmp_path / "PINS.toml"
    pins.write_text(f"""
[tools.active]
version = "43.00B261030"
[knoxmap]
tag = "1.8.5.5"
[trees.knoxmap]
dir = "{FAKE.as_posix()}"
[trees.tools_active]
dir = "{(FAKE / 'tools').as_posix()}"
[external.worlded_cli]
path = "{(FAKE / 'tools' / 'bin' / 'PZWorldEd_cli.exe').as_posix()}"
[external.osm_pbf]
path = "{(FAKE / 'extract.osm.pbf').as_posix()}"
[knoxmap_venv]
status = "locked"
venv_python = "{pathlib.Path(sys.executable).as_posix()}"
""", encoding="utf-8")
    cfg = tmp_path / "knoxmap.yaml"
    cfg.write_text(CFG, encoding="utf-8")
    monkeypatch.setattr(build.pins, "check", lambda p, allow_pending_venv=False: ([], 1))
    calls = []
    real_popen, real_run = subprocess.Popen, subprocess.run

    class Spy(real_popen):
        def __init__(self, argv, *a, **k):
            calls.append(list(argv))
            super().__init__(argv, *a, **k)
    monkeypatch.setattr(build.subprocess, "Popen", Spy)

    def run(argv, *a, **k):
        calls.append(list(argv))
        return real_run(argv, *a, **k)
    monkeypatch.setattr(build.subprocess, "run", run)
    return pins, cfg, tmp_path, calls


def test_pins_failure_aborts_before_any_subprocess(env, monkeypatch):
    pins, cfg, tmp, calls = env
    monkeypatch.setattr(build.pins, "check", lambda p, allow_pending_venv=False: ([("knoxmap_venv", "pending")], 1))
    with pytest.raises(build.BuildError, match="pins verify failed"):
        build.build(pins, cfg, tmp / "w")
    assert calls == []
    assert build._cmd_build(type("A", (), dict(pins=pins, config=cfg, work=str(tmp / "w2"), cells=None, check_repeat=False,
                                               project=None, mod_id=None))) == 1
    assert calls == []


def test_offline_env_and_auto_update_off(env):
    pins, cfg, tmp, _ = env
    w = build.build(pins, cfg, tmp / "w")
    e = json.loads((w / "knoxmap" / "output" / "fakemap" / "env.json").read_text())
    assert e["KNOXMAP_PBF_FILE"].endswith("extract.osm.pbf") and e["KNOXMAP_OSM_SOURCE"] == "extract"
    assert e["HTTP_PROXY"] == e["HTTPS_PROXY"] == "http://127.0.0.1:9"
    assert e["NO_PROXY"] == "127.0.0.1,localhost" and e["KNOXMAP_NO_DISCORD"] == "1"
    assert json.loads((w / "knoxmap" / "knoxmap_config.json").read_text())["auto_update"] is False


def test_manifest_is_deterministic_across_runs(env):
    pins, cfg, tmp, _ = env
    m1 = json.loads((build.build(pins, cfg, tmp / "a") / "build-record.json").read_text())["manifest"]
    m2 = json.loads((build.build(pins, cfg, tmp / "b") / "build-record.json").read_text())["manifest"]
    assert m1 == m2 and list(m1) == sorted(m1)
    assert {pathlib.Path(k).suffix for k in m1} == {".bmp", ".pzw", ".tbx"}


def test_network_in_log_fails_and_server_is_killed(env, monkeypatch):
    pins, cfg, tmp, _ = env
    monkeypatch.setenv("FAKE_NETWORK", "1")
    procs = []
    orig = build.Runner.serve

    def serve(self):
        p, port = orig(self)
        procs.append(p)
        return p, port
    monkeypatch.setattr(build.Runner, "serve", serve)
    with pytest.raises(build.BuildError, match="network use"):
        build.build(pins, cfg, tmp / "w")
    assert procs and all(p.poll() is not None for p in procs)


def test_server_killed_when_generate_fails(env, monkeypatch):
    pins, cfg, tmp, _ = env
    procs = []
    orig = build.Runner.serve

    def serve(self):
        p, port = orig(self)
        procs.append(p)
        return p, port
    monkeypatch.setattr(build.Runner, "serve", serve)
    monkeypatch.setattr(build, "_http", lambda *a, **k: (_ for _ in ()).throw(build.BuildError("boom")))
    with pytest.raises(build.BuildError):
        build.build(pins, cfg, tmp / "w")
    assert procs[0].poll() is not None


def test_map_name_is_explicit(env):
    pins, cfg, tmp, _ = env
    w = build.build(pins, cfg, tmp / "w")
    assert json.loads((w / "knoxmap" / "output" / "fakemap" / "request.json").read_text())["mapName"] == "fakemap"
    cfg.write_text(CFG.replace("map_name: fakemap\n", ""), encoding="utf-8")
    with pytest.raises(build.BuildError, match="map_name"):
        build.build(pins, cfg, tmp / "w2")
    cfg.write_text(CFG.replace("fakemap", "../evil"), encoding="utf-8")
    with pytest.raises(build.BuildError, match="map_name"):
        build.build(pins, cfg, tmp / "w3")


def test_uses_locked_venv_python_never_setup(env):
    pins, cfg, tmp, calls = env
    build.build(pins, cfg, tmp / "w")
    assert calls and all(c[0] == sys.executable and c[1:3] == ["-I", "-B"] for c in calls)
    assert not any("knoxmap_setup" in " ".join(c) for c in calls)


def test_record_and_payload_and_failed_compile_has_no_payload(env):
    pins, cfg, tmp, _ = env
    w = build.build(pins, cfg, tmp / "w")
    r = json.loads((w / "build-record.json").read_text())
    assert {"payload", "manifest", "transformations", "tools_version", "knoxmap_tag"} <= set(r)
    assert r["tools_version"] == "43.00B261030" and r["knoxmap_tag"] == "1.8.5.5"
    assert (w / "payload" / "mod.info").is_file() and pathlib.Path(r["payload"]) == w / "payload"
    with pytest.raises(build.BuildError, match="compile failed"):
        build.build(pins, cfg, tmp / "bad", cells="99,99,99,99")  # Test 8: --cells override forces the failure
    assert not (tmp / "bad" / "payload").exists() and not (tmp / "bad" / "build-record.json").exists()
    assert build._cmd_build(type("A", (), dict(pins=pins, config=cfg, work=str(tmp / "bad2"), cells="99,99,99,99",
                                               check_repeat=False, project=None, mod_id=None))) == 1


def test_hand_authored_project(env, monkeypatch):
    pins, cfg, tmp, calls = env
    fake_cli = tmp / "fake_cli.py"
    fake_cli.write_text("import sys,pathlib\n"
                        "p=pathlib.Path(sys.argv[1].split('=',1)[1]).parent/'lots';p.mkdir(exist_ok=True)\n"
                        "(p/'0_0.lotheader').write_bytes(b'h')\n", encoding="utf-8")
    monkeypatch.setattr(build, "cli_argv", lambda exe: [sys.executable, str(fake_cli)])
    proj = tmp / "mine" / "mine.pzw"
    proj.parent.mkdir()
    proj.write_text("<world/>", encoding="utf-8")
    w = build.build(pins, cfg, tmp / "w", project=proj, mod_id="minemod", cells="0,0,0,0")
    r = json.loads((w / "build-record.json").read_text())
    assert "hand-authored project" in r["transformations"] and (w / "payload" / "mod.info").is_file()
    assert not any("app.app.run" in " ".join(c) or "knoxbuild" in " ".join(c) for c in calls)
    with pytest.raises(build.BuildError, match="existing .pzw"):
        build.build(pins, cfg, tmp / "w2", project=tmp / "nope.pzw", mod_id="x")


def test_basement_settings_reach_generate(env):
    pins, cfg, tmp, _ = env
    cfg.write_text(CFG.replace('{landcover: "off"}', '{landcover: "off", basement_share: 0, max_basement_depth: 0}'), encoding="utf-8")
    w = build.build(pins, cfg, tmp / "w")
    s = json.loads((w / "knoxmap" / "output" / "fakemap" / "request.json").read_text())["settings"]
    assert s["max_basement_depth"] == 0 and s["basement_share"] == 0
    real = build.load_cfg(ROOT / "config" / "knoxmap.yaml")["settings"]
    assert real["max_basement_depth"] == 0
