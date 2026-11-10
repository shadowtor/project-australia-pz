"""PINS.toml verify/fetch/safe-extract. Fail closed; nothing downloaded or vendored is ever executed or imported."""
import hashlib
import os
import pathlib
import platform
import re
import sys
import tomllib
import urllib.request
import zipfile


def _sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _norm(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def tree_manifest(root, skip_pyc=False, exclude=()):
    """Sorted `relpath sha256` lines (forward slashes). skip_pyc ignores __pycache__ and *.pyc;
    exclude skips relative dir prefixes (e.g. a venv living inside the tree)."""
    root = pathlib.Path(root)
    lines = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(root)
        if any(rel.as_posix().startswith(e.rstrip('/') + '/') for e in exclude):
            continue
        if skip_pyc and ("__pycache__" in rel.parts or p.suffix == ".pyc"):
            continue
        lines.append(f"{rel.as_posix()} {_sha(p)}")
    return "".join(l + "\n" for l in sorted(lines))


def safe_extract(zip_path, dest):
    """Extract into a new or empty dest; any member escaping dest raises before anything is written."""
    dest = pathlib.Path(dest)
    if dest.exists() and (not dest.is_dir() or any(dest.iterdir())):
        raise ValueError(f"extract target not new/empty: {dest}")
    dest.mkdir(parents=True, exist_ok=True)
    root = dest.resolve()
    with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
            t = (root / name).resolve()
            if t != root and root not in t.parents:
                raise ValueError(f"zip member escapes target: {name}")
        zf.extractall(root)


def fetch(url, dest, sha256=None, md5=None):
    """Stream url to dest via temp name, hashing as it goes; delete and raise on mismatch. Returns sha256."""
    dest = pathlib.Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".part")
    h, m = hashlib.sha256(), hashlib.md5()
    try:
        with urllib.request.urlopen(url) as r, open(tmp, "wb") as f:
            for chunk in iter(lambda: r.read(1 << 20), b""):
                h.update(chunk)
                m.update(chunk)
                f.write(chunk)
        got = h.hexdigest()
        if sha256 and got != sha256:
            raise ValueError(f"sha256 mismatch for {url}: {got}")
        if md5 and m.hexdigest() != md5:
            raise ValueError(f"md5 mismatch for {url}: {m.hexdigest()}")
        os.replace(tmp, dest)
        return got
    finally:
        tmp.unlink(missing_ok=True)


def _path(base, s):
    p = pathlib.Path(s)
    return p if p.is_absolute() else base / p


def _check_game(g, base, bad):
    mp = _path(base, g.get("manifest_path", ""))
    if g.get("branch") != "stable":
        bad.append(("game", "branch is not stable"))
    if not mp.is_file():
        return bad.append(("game", f"appmanifest missing: {mp}"))
    t = mp.read_text(encoding="utf-8", errors="replace")
    b = re.search(r'"buildid"\s+"(\d+)"', t)
    beta = re.search(r'"BetaKey"\s+"([^"]*)"', t)
    if not b or b.group(1) != str(g.get("buildid")):
        bad.append(("game", f"buildid {b.group(1) if b else None} != pinned {g.get('buildid')}"))
    if beta and beta.group(1):
        bad.append(("game", f"BetaKey is '{beta.group(1)}', expected stable (empty)"))


def _check_zip(name, e, base, bad):
    p = _path(base, e.get("zip", ""))
    if not p.is_file():
        bad.append((name, f"missing {p}"))
    elif _sha(p) != e.get("sha256"):
        bad.append((name, "sha256 mismatch"))


def _check_tools(t, base, bad):
    act, fb = t.get("active", {}), t.get("fallback", {})
    _check_zip("tools.active", act, base, bad)
    if fb:
        _check_zip("tools.fallback", fb, base, bad)
        if fb.get("status") not in ("inactive", "phase2_target"):
            bad.append(("tools.fallback", f"status {fb.get('status')!r}: silent switch (must be inactive/phase2_target)"))
    sel = act.get("selected_by")
    if sel == "user-approved-switch":
        ap = act.get("approval", {})
        if not (ap.get("date") and ap.get("reason") and ap.get("evidence") and _path(base, ap["evidence"]).exists()):
            bad.append(("tools.active", "user-approved-switch needs approval date, reason and existing evidence file"))
    elif sel != "user-decision-after-research":
        bad.append(("tools.active", f"selected_by {sel!r} not recognised"))


def base_manifest(home):
    """Sorted `relpath sha256` lines for the real base interpreter: python.exe, python3*.dll, vcruntime*.dll,
    and the Lib/ + DLLs/ trees (no __pycache__/*.pyc). Read-only; nothing is executed."""
    home = pathlib.Path(home)
    lines = [f"{p.name} {_sha(p)}" for pat in ("python.exe", "python3*.dll", "vcruntime*.dll") for p in home.glob(pat) if p.is_file()]
    for sub in ("Lib", "DLLs"):
        if (home / sub).is_dir():
            lines += [f"{sub}/{l}" for l in tree_manifest(home / sub, skip_pyc=True).splitlines()]
    return "".join(l + "\n" for l in sorted(set(lines)))


def _expand(s):
    """Expand %VAR% tokens (Windows style, any OS); an undefined variable leaves '%' behind -> None (fail closed)."""
    out = re.sub(r"%([^%]+)%", lambda m: os.environ.get(m.group(1), m.group(0)), s or "")
    return out if out and "%" not in out else None


def _under(p, d):
    p, d = os.path.normcase(os.path.realpath(p)), os.path.normcase(os.path.realpath(d))
    return p == d or p.startswith(d.rstrip("\\/") + os.sep)


def _check_base_python(v, base, bad):
    """The venv `home` may be a user-writable Store alias dir; trust only the pinned real install, hashed."""
    real = _expand(v.get("base_python_real_home"))
    if not real or not os.path.isdir(real):
        return bad.append(("knoxmap_venv", f"base_python_real_home missing or not a directory: {real!r}"))
    for env in ("LOCALAPPDATA", "USERPROFILE"):
        if os.environ.get(env) and _under(real, os.environ[env]):
            return bad.append(("knoxmap_venv", f"base_python_real_home {real!r} is under user-writable %{env}%"))
    man = _path(base, v.get("base_python_manifest", ""))
    if not man.is_file() or _sha(man) != v.get("base_python_manifest_sha256"):
        return bad.append(("knoxmap_venv", "base python manifest missing or sha256 mismatch"))
    if base_manifest(real) != man.read_text(encoding="utf-8"):
        bad.append(("knoxmap_venv", "real base interpreter files differ from base python manifest (added/altered/removed)"))


def _check_launcher(v, root, base, bad):
    """Everything in the venv outside Lib/site-packages (launcher exes, pyvenv.cfg): read and hashed, never run."""
    cfg = root / "pyvenv.cfg"
    if not cfg.is_file():
        return bad.append(("knoxmap_venv", "pyvenv.cfg missing"))
    if _sha(cfg) != v.get("pyvenv_cfg_sha256"):
        bad.append(("knoxmap_venv", "pyvenv.cfg sha256 mismatch"))
    kv = {}
    for line in cfg.read_text(encoding="utf-8", errors="replace").splitlines():
        k, sep, val = line.partition("=")
        if sep:
            kv[k.strip().lower()] = val.strip()
    if kv.get("include-system-site-packages", "").lower() != "false":
        bad.append(("knoxmap_venv", "pyvenv.cfg include-system-site-packages is not false"))
    pinned_home = _expand(v.get("base_python_home"))
    if not pinned_home or os.path.normcase(os.path.normpath(kv.get("home", ""))) != os.path.normcase(os.path.normpath(pinned_home)):
        bad.append(("knoxmap_venv", f"pyvenv.cfg home {kv.get('home')!r} != pinned base_python_home"))
    _check_base_python(v, base, bad)
    man = _path(base, v.get("launcher_manifest", ""))
    if not man.is_file() or _sha(man) != v.get("launcher_manifest_sha256"):
        return bad.append(("knoxmap_venv", "launcher manifest missing or sha256 mismatch"))
    if tree_manifest(root, skip_pyc=True, exclude=("Lib/site-packages",)) != man.read_text(encoding="utf-8"):
        bad.append(("knoxmap_venv", "venv files outside Lib/site-packages differ from launcher manifest (added/altered/removed)"))


def _check_venv(v, base, allow_pending, bad):
    if v.get("status") != "locked":
        if not (v.get("status") == "pending" and allow_pending):
            bad.append(("knoxmap_venv", f"status {v.get('status')!r}, not locked"))
        return
    req = _path(base, v.get("requirements_file", ""))
    if not req.is_file() or _sha(req) != v.get("requirements_sha256"):
        return bad.append(("knoxmap_venv", "requirements file missing or sha256 mismatch"))
    want = {}
    for line in req.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "--hash=sha256:" not in line:
            bad.append(("knoxmap_venv", f"requirement without --hash=sha256: {line[:60]}"))
        m = re.match(r"([A-Za-z0-9._-]+)==(\S+)", line)
        if m:
            want[_norm(m.group(1))] = m.group(2)
    root = _path(base, v.get("venv_python", "")).parent.parent
    _check_launcher(v, root, base, bad)
    sp = root / "Lib" / "site-packages"
    if not sp.is_dir():
        return bad.append(("knoxmap_venv", f"site-packages missing: {sp}"))
    have = {}
    for d in sp.glob("*.dist-info"):  # METADATA read as text, nothing imported
        meta = (d / "METADATA").read_text(encoding="utf-8", errors="replace") if (d / "METADATA").is_file() else ""
        n, ver = re.search(r"^Name: (.+)$", meta, re.M), re.search(r"^Version: (.+)$", meta, re.M)
        if n and ver:
            have[_norm(n.group(1).strip())] = ver.group(1).strip()
    if have != want:
        diff = sorted(set(have.items()) ^ set(want.items()))
        bad.append(("knoxmap_venv", f"installed set != reviewed list: {diff}"))
    stray = [p.relative_to(sp).as_posix() for p in sp.rglob("*.pyc") if p.parent.name != "__pycache__"]
    if stray:  # sourceless bytecode runs without any source to hash
        bad.append(("knoxmap_venv", f"sourceless .pyc outside __pycache__: {stray[:5]}"))
    man = tree_manifest(sp, skip_pyc=True)
    if hashlib.sha256(man.encode()).hexdigest() != v.get("site_packages_manifest_sha256"):
        bad.append(("knoxmap_venv", "site-packages manifest hash mismatch"))


def check(pins_path, allow_pending_venv=False):
    """Return (mismatches, items_checked)."""
    pins_path = pathlib.Path(pins_path)
    base = pins_path.parent
    d = tomllib.loads(pins_path.read_text(encoding="utf-8"))
    bad, n = [], 0
    for rel, want in d.get("files", {}).items():
        n += 1
        p = base / rel
        if not p.is_file():
            bad.append((rel, "missing"))
        elif _sha(p) != want:
            bad.append((rel, "sha256 mismatch"))
    for name, e in d.get("external", {}).items():  # large downloads outside the repo
        n += 1
        p = _path(base, e.get("path", ""))
        if not p.is_file():
            bad.append((name, f"missing {p}"))
        else:
            if _sha(p) != e.get("sha256"):
                bad.append((name, "sha256 mismatch"))
            if e.get("md5") and hashlib.md5(p.read_bytes()).hexdigest() != e["md5"]:
                bad.append((name, "md5 mismatch"))
    for name, t in d.get("trees", {}).items():
        n += 1
        root, man = _path(base, t.get("dir", "")), _path(base, t.get("manifest", ""))
        if not root.is_dir() or not man.is_file():
            bad.append((name, "tree or manifest missing"))
        elif tree_manifest(root, exclude=t.get("exclude", ())) != man.read_text(encoding="utf-8"):
            bad.append((name, "tree manifest mismatch (added/altered/removed file)"))
    if "game" in d:
        n += 1
        _check_game(d["game"], base, bad)
    if "tools" in d:
        n += 1
        _check_tools(d["tools"], base, bad)
    if "python" in d:
        n += 1
        py = d["python"]
        if not platform.python_version().startswith(str(py.get("version", "\0"))):
            bad.append(("python", f"running {platform.python_version()} != pinned {py.get('version')}"))
        lock = _path(base, py.get("requirements_lock", ""))
        if lock.is_file() and _sha(lock) != py.get("requirements_lock_sha256"):
            bad.append(("python", "requirements.lock sha256 mismatch"))
        elif not lock.is_file():
            bad.append(("python", "requirements.lock missing"))
    if "knoxmap_venv" in d:
        n += 1
        _check_venv(d["knoxmap_venv"], base, allow_pending_venv, bad)
    return bad, n


def verify(pins_path, allow_pending_venv=False):
    """List of (item, reason) mismatches; empty means everything verified."""
    return check(pins_path, allow_pending_venv)[0]


def venv_cmd(pins_path):
    """argv prefix for any run against the locked KnoxMap venv: isolated, no bytecode writes (-B)."""
    v = tomllib.loads(pathlib.Path(pins_path).read_text(encoding="utf-8"))["knoxmap_venv"]
    return [str(_path(pathlib.Path(pins_path).parent, v["venv_python"])), "-I", "-B"]


def _cmd_verify(a):
    bad, n = check(a.pins, a.allow_pending_venv)
    for item, why in bad:
        print(f"PINS FAIL {item}: {why}")
    if bad:
        return 1
    print(f"pins verify OK: all {n} items verified")
    return 0


def _cmd_fetch(a):
    e = tomllib.loads(pathlib.Path(a.pins).read_text(encoding="utf-8"))["external"][a.name]
    dest = _path(pathlib.Path(a.pins).parent, e["path"])
    got = fetch(e["url"], dest, e.get("sha256"), e.get("md5"))
    print(f"fetched {a.name} -> {dest} sha256={got}")
    return 0


def _cmd_manifest(a):
    m = tree_manifest(a.dir, skip_pyc=a.skip_pyc)
    if a.out:
        pathlib.Path(a.out).write_text(m, encoding="utf-8", newline="\n")
    else:
        sys.stdout.write(m)
    return 0


def register(subparsers):
    p = subparsers.add_parser("pins", help="verify/fetch/manifest pinned inputs")
    s = p.add_subparsers(dest="pins_cmd", required=True)
    v = s.add_parser("verify")
    v.add_argument("--pins", default="PINS.toml")
    v.add_argument("--allow-pending-venv", action="store_true")
    v.set_defaults(func=_cmd_verify)
    f = s.add_parser("fetch")
    f.add_argument("name")
    f.add_argument("--pins", default="PINS.toml")
    f.set_defaults(func=_cmd_fetch)
    m = s.add_parser("manifest")
    m.add_argument("dir")
    m.add_argument("--out")
    m.add_argument("--skip-pyc", action="store_true")
    m.set_defaults(func=_cmd_manifest)
