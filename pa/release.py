import hashlib
import os
import pathlib
import re
import shutil


def tree_version(src):
    h = hashlib.sha256()
    for p in sorted(pathlib.Path(src).rglob("*")):
        if p.is_file():
            h.update(p.relative_to(src).as_posix().encode() + b"\0" + p.read_bytes())
    return h.hexdigest()[:12]


def release(src, work):
    """staging/<ver> -> os.replace -> releases/<ver>, then current.txt via temp + os.replace. Returns version."""
    work = pathlib.Path(work)
    ver = tree_version(src)
    staging, final = work / "staging" / ver, work / "releases" / ver
    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(src, staging)
    final.parent.mkdir(parents=True, exist_ok=True)
    if final.exists():  # same content already released
        shutil.rmtree(staging)
    else:
        os.replace(staging, final)
    tmp = work / "current.txt.tmp"
    tmp.write_text(ver + "\n", encoding="utf-8")
    os.replace(tmp, work / "current.txt")
    return ver


# --- atomic release store (BUILD-04): staging/ -> gates -> releases/<ver> -> current.txt; installer reads current.txt only ---
VERSION_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")


class ReleaseError(Exception):
    pass


def safe_name(s, what="version"):
    """Single path component only (T-01-12): no separators, no '..', no empty."""
    if not isinstance(s, str) or not VERSION_RE.fullmatch(s) or ".." in s:
        raise ReleaseError(f"bad {what} {s!r}: need one path component [A-Za-z0-9._-]")
    return s


def _atomic_write(path, text):
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def read_current(root):
    """Return the validated current release name, or None when nothing is released."""
    f = pathlib.Path(root) / "current.txt"
    if not f.is_file():
        return None
    return safe_name(f.read_text(encoding="utf-8").strip(), "current.txt")


def _quarantine(staging, root, ver):
    dest = pathlib.Path(root) / "staging-failed" / ver
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        shutil.rmtree(dest)
    if staging.exists():
        os.replace(staging, dest)
    return dest


def build_release(generate, compile_, gates, root, version):
    """Run generate and compile into staging/<ver>, then gates; any failure quarantines staging and leaves
    current.txt and releases/* untouched. generate/compile_ take the staging dir; each gate takes it and returns
    a list of findings (truthy = fail). Returns the version."""
    root, version = pathlib.Path(root), safe_name(version)
    staging, final = root / "staging" / version, root / "releases" / version
    if final.exists():
        raise ReleaseError(f"release {version} already exists; releases are immutable")
    for d in (root / "staging", root / "releases"):
        d.mkdir(parents=True, exist_ok=True)
    if (root / "staging").stat().st_dev != (root / "releases").stat().st_dev:
        raise ReleaseError("staging and releases must share a volume for atomic os.replace")
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir()
    try:
        generate(staging)
        compile_(staging)
        for g in gates:
            findings = g(staging)
            if findings:
                raise ReleaseError(f"gate failed: {findings[0]}" + (f" (+{len(findings) - 1} more)" if len(findings) > 1 else ""))
    except BaseException:
        _quarantine(staging, root, version)
        raise
    os.replace(staging, final)
    _atomic_write(root / "current.txt", version + "\n")
    return version


def install(root, mods_dir, mod_id):
    """Copy releases/<current> to <mods>/<id>.new, then swap it in. A failed copy leaves the installed mod intact."""
    root, mods_dir, mod_id = pathlib.Path(root), pathlib.Path(mods_dir), safe_name(mod_id, "mod id")
    cur = read_current(root)
    if cur is None:
        raise ReleaseError("no current.txt: nothing released")
    src = (root / "releases" / cur).resolve()
    if (root / "releases").resolve() not in src.parents or not src.is_dir():
        raise ReleaseError(f"current release {cur!r} is not under releases/")
    mods_dir.mkdir(parents=True, exist_ok=True)
    new, dest, old = mods_dir / f"{mod_id}.new", mods_dir / mod_id, mods_dir / f"{mod_id}.old"
    for d in (new, old):
        if d.exists():
            shutil.rmtree(d)
    try:
        shutil.copytree(src, new)
    except BaseException:
        shutil.rmtree(new, ignore_errors=True)
        raise
    if dest.exists():  # Windows cannot rename over a non-empty dir: move aside, swap, drop
        os.replace(dest, old)
    os.replace(new, dest)
    shutil.rmtree(old, ignore_errors=True)
    return dest


def _ledger_gate(staging):
    """T-01-14: the ledger is a hard prerequisite; a missing or broken pa.ledger fails the release, never skips."""
    try:
        import pa.ledger as ledger
    except ImportError as e:
        raise ReleaseError(f"pa.ledger unavailable: {e}") from e
    return ledger.gate(staging)


def _config_gates(world, cfg_file):
    """Optional --gates-config yaml: {palette: {bmp: <rel to world>, palette: <rel to world>}}. Paths confined to world."""
    import yaml
    from pa import edits, gates
    world = pathlib.Path(world)
    cfg = yaml.safe_load(pathlib.Path(cfg_file).read_text(encoding="utf-8")) or {}
    if not isinstance(cfg, dict):
        raise ReleaseError("gates config must be a mapping")
    out = []
    p = cfg.get("palette")
    if p is not None:
        bmp, pal = edits.inside(world / str(p["bmp"]), world), edits.inside(world / str(p["palette"]), world)
        out.append(lambda _s: [f.line() for f in gates.palette_gate(bmp, gates.load_palette(pal))])
    return out


def _cmd_release(a):
    payload = pathlib.Path(a.payload)
    if not payload.is_dir() or not any(payload.iterdir()):
        print(f"RELEASE FAIL: payload {payload} is missing or empty")
        return 1
    gates = [_ledger_gate]
    try:
        if a.world or a.gates_config:
            if not (a.world and a.gates_config):
                raise ReleaseError("--world and --gates-config go together")
            gates = _config_gates(a.world, a.gates_config) + gates
        ver = build_release(lambda s: shutil.copytree(payload, s, dirs_exist_ok=True), lambda s: None, gates, a.root, a.version)
    except (ReleaseError, ValueError, OSError, KeyError, TypeError) as e:
        print(f"RELEASE FAIL: {e}")
        return 1
    print("RELEASE", ver)
    return 0


def _cmd_install(a):
    try:
        print("INSTALLED", install(a.root, a.mods_dir, a.mod_id))
    except (ReleaseError, OSError) as e:
        print(f"INSTALL FAIL: {e}")
        return 1
    return 0


def register(subparsers):
    r = subparsers.add_parser("release", help="stage a build payload, gate it, promote atomically")
    r.add_argument("--payload", required=True)
    r.add_argument("--version", required=True)
    r.add_argument("--root", default="release")
    r.add_argument("--world")
    r.add_argument("--gates-config")
    r.set_defaults(func=_cmd_release)
    i = subparsers.add_parser("install", help="copy releases/<current> into the mods dir atomically")
    i.add_argument("--root", default="release")
    i.add_argument("--mod-id", required=True)
    i.add_argument("--mods-dir", default=os.path.join(os.environ.get("USERPROFILE", "~"), "Zomboid", "mods"))
    i.set_defaults(func=_cmd_install)
