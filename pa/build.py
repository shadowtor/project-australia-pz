"""Offline KnoxMap driver (D-08, BUILD-01). KnoxMap is a black box: generate, knoxbuild, compile, package.

Runs only the PINS-locked venv python, only after `pins verify` passes, on a fresh copy of the verified trees
(the vendored trees are never written to), with no network and the server bound to 127.0.0.1 and always killed.
"""
import hashlib
import http.client
import json
import os
import pathlib
import re
import shutil
import socket
import subprocess
import sys
import time
import tomllib
import urllib.error
import urllib.request

import yaml

from pa import edits, pins

ROOT = pathlib.Path(__file__).resolve().parent.parent
NET_RE = re.compile(r"overpass|nominatim|max retries exceeded|getaddrinfo|proxyerror|connectionerror|"
                    r"newconnectionerror|name resolution", re.I)
NAME_RE = re.compile(r"[A-Za-z0-9_]{1,40}")
PRELUDE = "import sys;sys.path.insert(0,sys.argv[1]);"  # -I drops the script dir, so the launcher adds the tree itself
SERVER = PRELUDE + "import app;app.app.run(host='127.0.0.1',port=int(sys.argv[2]),debug=False)"
KNOXBUILD = PRELUDE + "from knoxbuild.build import main;sys.exit(main([sys.argv[2]]))"
# one attempt and a short batch timeout so a hidden modal dialog fails fast instead of hanging 30 min x 3
COMPILE = PRELUDE + ("import json;import tools.compile_map as c;c.BATCH_TIMEOUT=int(sys.argv[5]);c.BATCH_ATTEMPTS=1;"
                     "n=c.compile_map(sys.argv[2],exe=sys.argv[3],only_cells=json.loads(sys.argv[4]) or None,backend='worlded');"
                     "print('compiled',n);sys.exit(0 if n else 3)")
# Only the named KnoxMap Setup step (tile artwork + PZTools.ini); never Setup's downloads or pip. patch_rules is stubbed
# out because it spawns a bare sys.executable; the wrapper runs the two patch scripts itself with -I -B.
PREPARE = PRELUDE + ("import pathlib,knoxmap_setup as s,knoxpaths;s.patch_rules=lambda t:None;"
                     "g=knoxpaths.pz_install_from(sys.argv[3]);assert g,'no Project Zomboid install at '+sys.argv[3];"
                     "s.configure_tools(pathlib.Path(sys.argv[2]),g)")
RULE_SCRIPTS = ("patch_rules_b42_trees.py", "patch_rules_roads.py")
DEFAULT_TIMEOUT = 300
PACKAGE = PRELUDE + ("from tools.make_map_mod import main;"
                     "sys.exit(main([sys.argv[2],'--name',sys.argv[3],'--id',sys.argv[4],'--mods-dir',sys.argv[5]]))")


class BuildError(Exception):
    pass


def load_cfg(path):
    """Config is untrusted yaml: validate everything that reaches a path, a URL body or a command line."""
    c = yaml.safe_load(pathlib.Path(path).read_text(encoding="utf-8"))
    if not isinstance(c, dict):
        raise BuildError("knoxmap config must be a mapping")
    for k in ("map_name", "mod_id"):
        if not isinstance(c.get(k), str) or not NAME_RE.fullmatch(c[k]):
            raise BuildError(f"{k} must be an explicit name matching [A-Za-z0-9_]{{1,40}}")
    if not isinstance(c.get("mod_name"), str) or not c["mod_name"].strip():
        raise BuildError("mod_name required")
    b = c.get("bbox")
    if not (isinstance(b, dict) and all(type(b.get(k)) in (int, float) for k in ("south", "west", "north", "east"))):
        raise BuildError("bbox needs numeric south/west/north/east")
    if type(c.get("meters_per_tile")) not in (int, float):
        raise BuildError("meters_per_tile must be numeric")
    c["cells"] = [_cells(x) for x in (c.get("cells") or [])]
    if not isinstance(c.get("settings", {}), dict):
        raise BuildError("settings must be a mapping")
    pt = c.get("prepare_tools")
    if pt is not None and not (isinstance(pt, dict) and isinstance(pt.get("game_dir"), str)):
        raise BuildError("prepare_tools needs game_dir")
    if type(c.get("compile_timeout_s", 300)) is not int or c.get("compile_timeout_s", 300) < 10:
        raise BuildError("compile_timeout_s must be an int >= 10")
    return c


def _cells(v):
    v = list(v) if isinstance(v, (list, tuple)) else str(v).split(",")
    try:
        r = [int(x) for x in v]
    except (TypeError, ValueError):
        raise BuildError(f"bad cells {v!r}: want x0,y0,x1,y1 integers") from None
    if len(r) != 4:
        raise BuildError(f"bad cells {v!r}: want x0,y0,x1,y1")
    return r


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def manifest(d):
    """Sorted `relpath sha256` of the BMP/.pzw/.tbx outputs (success criterion 1, Pitfall 4; lotpacks not asserted)."""
    d = pathlib.Path(d)
    return {p.relative_to(d).as_posix(): sha_file(p)
            for p in sorted(d.rglob("*")) if p.is_file() and p.suffix.lower() in (".bmp", ".pzw", ".tbx")}


def _paths(pins_path):
    t = tomllib.loads(pathlib.Path(pins_path).read_text(encoding="utf-8"))
    base = pathlib.Path(pins_path).parent
    p = lambda s: pathlib.Path(s) if os.path.isabs(s) else base / s
    return dict(
        km=p(t["trees"]["knoxmap"]["dir"]) / "KnoxMap", tools=p(t["trees"]["tools_active"]["dir"]),
        cli=p(t["external"]["worlded_cli"]["path"]), pbf=p(t["external"]["osm_pbf"]["path"]),
        tools_version=t["tools"]["active"]["version"], tag=t["knoxmap"]["tag"],
        data_dir=pathlib.Path(t.get("data_dir", "")) if t.get("data_dir") else None)


def _env(work, km, tools, cli, pbf):
    e = dict(os.environ)
    for k in list(e):
        if k.lower() in ("http_proxy", "https_proxy", "all_proxy", "no_proxy"):
            del e[k]
    e.update(KNOXMAP_PBF_FILE=str(pbf), KNOXMAP_OSM_SOURCE="extract", KNOXMAP_NO_DISCORD="1",
             PZ_MAPPING_TOOLS=str(tools), PZWORLDED_CLI=str(cli),
             HTTP_PROXY="http://127.0.0.1:9", HTTPS_PROXY="http://127.0.0.1:9", ALL_PROXY="http://127.0.0.1:9",
             http_proxy="http://127.0.0.1:9", https_proxy="http://127.0.0.1:9", all_proxy="http://127.0.0.1:9",
             NO_PROXY="127.0.0.1,localhost", no_proxy="127.0.0.1,localhost")
    return e


def run_tree(argv, cwd, env, log, timeout):
    """Run to completion or kill the whole process tree on timeout (a hidden dialog must fail fast)."""
    p = subprocess.Popen(argv, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT)
    try:
        return p.wait(timeout)
    except subprocess.TimeoutExpired:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True)
        p.kill(); p.wait(10)
        raise BuildError(f"step timed out after {timeout}s and its process tree was killed: {' '.join(map(str, argv[3:6]))}") from None


class Runner:
    def __init__(self, py, km, work, env, log):
        self.py, self.km, self.work, self.env, self.log = py, km, work, env, log

    def run(self, code, *args, timeout=3600):
        argv = self.py + ["-c", code, str(self.km), *map(str, args)]
        self.log.write(f"\n$ {' '.join(argv[:3])} ... {' '.join(map(str, args))}\n".encode()); self.log.flush()
        return run_tree(argv, self.work, self.env, self.log, timeout)

    def serve(self):
        s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
        return subprocess.Popen(self.py + ["-c", SERVER, str(self.km), str(port)], cwd=self.work, env=self.env,
                                stdout=self.log, stderr=subprocess.STDOUT), port


def _http(port, method, path, body=None, timeout=3600):
    # explicit empty ProxyHandler: loopback only, never through the (poisoned) proxy
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", method=method,
                                 data=None if body is None else json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with op.open(req, timeout=timeout) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        raise BuildError(f"{method} {path} -> {e.code}: {e.read()[:300]!r}") from None


def _wait(proc, port, secs=90):
    t = time.time()
    while time.time() - t < secs:
        if proc.poll() is not None:
            raise BuildError(f"KnoxMap server exited early (code {proc.returncode})")
        try:
            http.client.HTTPConnection("127.0.0.1", port, timeout=2).request("GET", "/")
            return
        except OSError:
            time.sleep(0.5)
    raise BuildError("KnoxMap server did not start")


def _stop(proc):
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(10)
        except subprocess.TimeoutExpired:
            proc.kill(); proc.wait(10)


def cli_argv(exe):
    return [str(exe)]  # separate so tests can swap in a fake compiler


def _copy_trees(work, P):
    """Copy verified trees into the fresh work dir; the vendored trees stay read-only."""
    km = work / "knoxmap"
    shutil.copytree(P["km"], km, ignore=shutil.ignore_patterns(".venv", "output", "cache", "__pycache__"))
    (km / "output").mkdir()
    tools = work / "tools"
    shutil.copytree(P["tools"], tools)
    (tools / "bin").mkdir(exist_ok=True)
    cli = tools / "bin" / pathlib.Path(P["cli"]).name
    shutil.copy2(P["cli"], cli)
    (km / "knoxmap_config.json").write_text(json.dumps({"auto_update": False}), encoding="utf-8")
    return km, tools, cli


def prepare_tools(R, km, tools, pt, work):
    """Configure the WORK COPY of the tools (tile artwork, PZTools.ini, Rules.txt patches) and write prepare-record.json.
    Plan 01-02 locked the venv but not tools configuration; this is that gap, made explicit and reproducible."""
    game = pathlib.Path(pt["game_dir"])
    if not game.is_dir():
        raise BuildError(f"prepare_tools.game_dir {game} is not a directory")
    if R.run(PREPARE, tools, game, timeout=pt.get("timeout_s", 1800)):
        raise BuildError("prepare-tools: tile setup failed (see build.log)")
    for sc in RULE_SCRIPTS:
        if run_tree(R.py + [str(km / "worlded" / sc), str(tools)], work, R.env, R.log, 300):
            raise BuildError(f"prepare-tools: {sc} failed (see build.log)")
    ini, rules, tilesets = tools / "settings" / "PZTools.ini", tools / "config" / "Rules.txt", tools / "config" / "Tilesets.txt"
    sheets = sorted((tools / "Tiles" / "2x").glob("*.png"))
    if "TilesDirectory=" not in ini.read_text(encoding="utf-8") or not sheets:
        raise BuildError("prepare-tools: PZTools.ini has no TilesDirectory or no tile sheets were extracted")
    if "KnoxMap road Yard bed_soil" not in rules.read_text(encoding="utf-8", errors="replace"):
        raise BuildError("prepare-tools: Rules.txt road rules were not applied")
    rec = dict(game_dir=str(game), tile_sheets=len(sheets), steps=["knoxmap_setup.configure_tools (tiles + PZTools.ini)", *RULE_SCRIPTS],
               sha256={"settings/PZTools.ini": sha_file(ini), "config/Rules.txt": sha_file(rules), "config/Tilesets.txt": sha_file(tilesets)})
    (work / "prepare-record.json").write_text(json.dumps(rec, indent=1), encoding="utf-8")
    return rec


def build(pins_path, cfg_path, work=None, cells=None, project=None, mod_id=None):
    """Returns the work dir. Raises BuildError; the server is killed and a failed compile leaves no payload."""
    bad, _ = pins.check(pins_path)  # fail closed before anything is spawned
    if bad:
        raise BuildError("pins verify failed: " + "; ".join(f"{i}: {w}" for i, w in bad[:5]))
    P, py = _paths(pins_path), pins.venv_cmd(pins_path)
    cfg = load_cfg(cfg_path)
    if project:
        mod_id = edits_name(mod_id)
        project = pathlib.Path(project)
        if not project.is_file() or project.suffix.lower() != ".pzw":
            raise BuildError(f"hand-authored project {project} is not an existing .pzw")
    else:
        mod_id = cfg["mod_id"]
    if work is None:
        dd = P["data_dir"] or pathlib.Path(yaml.safe_load((ROOT / "config" / "world.yaml").read_text(encoding="utf-8"))["data_dir"])
        work = dd / "work" / time.strftime("build-%Y%m%dT%H%M%S", time.gmtime())
    work = pathlib.Path(work)
    if work.exists() and any(work.iterdir()):
        raise BuildError(f"work dir {work} is not empty")
    work.mkdir(parents=True, exist_ok=True)
    km, tools, cli = _copy_trees(work, P)
    env = _env(work, km, tools, cli, P["pbf"])
    with open(work / "build.log", "wb") as log:
        R = Runner(py, km, work, env, log)
        steps, timeout = [], int(cfg.get("compile_timeout_s", DEFAULT_TIMEOUT))
        if cfg.get("prepare_tools"):
            rec = prepare_tools(R, km, tools, cfg["prepare_tools"], work)
            steps.append("prepare-tools (tiles, PZTools.ini, Rules.txt patches)")
        if project:
            out = project.parent
            c = [_cells(cells)] if cells else []
            steps.append("hand-authored project")
            a = cli_argv(cli) + [f"--generate-map={project}"] + ([f"--cells={','.join(map(str, c[0]))}"] if c else [])
            log.write(f"\n$ {' '.join(a)}\n".encode()); log.flush()
            if run_tree(a, work, env, log, timeout):
                raise BuildError("compile failed (see build.log)")
            name = mod_id
            mani = manifest(out)
        else:
            c = [_cells(cells)] if cells else cfg["cells"]
            name, out = cfg["map_name"], km / "output" / cfg["map_name"]
            proc, port = R.serve()
            try:
                _wait(proc, port)
                b = cfg["bbox"]
                _http(port, "POST", "/api/generate", dict(mapName=name, south=b["south"], west=b["west"], north=b["north"],
                                                         east=b["east"], metersPerTile=cfg["meters_per_tile"], settings=cfg.get("settings", {})))
                if cfg.get("standalone"):
                    _http(port, "POST", f"/api/placement/{name}", {"standalone": True})
            finally:
                _stop(proc)
            steps += ["knoxmap generate (osm extract, offline)", "knoxbuild"]
            if R.run(KNOXBUILD, out):
                raise BuildError("knoxbuild failed (see build.log)")
            mani = manifest(out)
            steps.append("worlded compile (PZWorldEd_cli, patched)")
            if R.run(COMPILE, out, cli, json.dumps(c), timeout, timeout=timeout + 120):
                raise BuildError("compile failed (see build.log)")
        _scan(work / "build.log")
        mods = work / "mods"
        if R.run(PACKAGE, out, cfg["mod_name"] if cfg else mod_id, mod_id, mods):
            raise BuildError("packaging failed (see build.log)")
        steps.append("make_map_mod")
    _scan(work / "build.log")
    shutil.copytree(edits.inside(mods / mod_id, mods), work / "payload")
    (work / "build-record.json").write_text(json.dumps(dict(
        payload=str(work / "payload"), manifest=mani, transformations=steps,
        tools_version=P["tools_version"], knoxmap_tag=P["tag"],
        prepare_tools=(rec if cfg.get("prepare_tools") else None)), indent=1), encoding="utf-8")
    return work


def edits_name(s):
    if not isinstance(s, str) or not NAME_RE.fullmatch(s):
        raise BuildError("--mod-id must match [A-Za-z0-9_]{1,40}")
    return s


def _scan(log):
    m = NET_RE.search(pathlib.Path(log).read_text(encoding="utf-8", errors="replace"))
    if m:
        raise BuildError(f"network use detected in KnoxMap log: {m.group(0)!r} (offline build must not touch the network)")


def _cmd_build(a):
    try:
        if bool(a.project) != bool(a.mod_id):
            raise BuildError("--project and --mod-id go together")
        w = build(a.pins, a.config, a.work, a.cells, a.project, a.mod_id)
        if a.check_repeat:
            if a.project:
                raise BuildError("--check-repeat applies to generated builds only")
            w2 = build(a.pins, a.config, None if not a.work else pathlib.Path(a.work).with_name(pathlib.Path(a.work).name + "-repeat"), a.cells)
            m1 = json.loads((w / "build-record.json").read_text())["manifest"]
            m2 = json.loads((w2 / "build-record.json").read_text())["manifest"]
            if m1 != m2:
                diff = sorted(k for k in set(m1) | set(m2) if m1.get(k) != m2.get(k))
                raise BuildError(f"repeat build differs in {len(diff)} file(s): {diff[:5]}")
    except (BuildError, OSError, subprocess.TimeoutExpired, KeyError, ValueError) as e:
        print(f"BUILD FAIL: {e}")
        return 1
    print("BUILD OK", w)
    return 0


def register(subparsers):
    b = subparsers.add_parser("build", help="offline KnoxMap build: generate, knoxbuild, compile, package")
    b.add_argument("--pins", default=str(ROOT / "PINS.toml"))
    b.add_argument("--config", default=str(ROOT / "config" / "knoxmap.yaml"))
    b.add_argument("--work")
    b.add_argument("--cells", help="x0,y0,x1,y1 overrides the config cell list")
    b.add_argument("--check-repeat", action="store_true")
    b.add_argument("--project", help="hand-authored .pzw: compile and package only")
    b.add_argument("--mod-id")
    b.set_defaults(func=_cmd_build)
