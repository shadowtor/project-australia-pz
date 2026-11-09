"""pins verify/fetch/extract: fail-closed supply-chain checks (T-01-04..07, T-01-32, T-01-SC)."""
import hashlib
import pathlib
import platform
import zipfile

import pytest

from pa import pins


def sha(b):
    return hashlib.sha256(b).hexdigest()


def write(p, data):
    p = pathlib.Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data if isinstance(data, bytes) else data.encode())
    return p


def check(p, **kw):
    return pins.verify(p, **kw)


# Test 1
def test_files_hash_and_flip(tmp_path):
    f = write(tmp_path / "a.bin", b"hello")
    (tmp_path / "PINS.toml").write_text(f'[files]\n"a.bin" = "{sha(b"hello")}"\n')
    assert check(tmp_path / "PINS.toml") == []
    f.write_bytes(b"hellp")
    bad = check(tmp_path / "PINS.toml")
    assert bad and bad[0][0] == "a.bin"


# Test 2
def acf(root, buildid, beta=None):
    extra = f'\t"UserConfig"\n\t{{\n\t\t"BetaKey"\t\t"{beta}"\n\t}}\n' if beta is not None else ""
    return write(root / "appmanifest_108600.acf", f'"AppState"\n{{\n\t"buildid"\t\t"{buildid}"\n{extra}}}\n')


def game_pins(root, buildid="26486631"):
    return (root / "PINS.toml").write_text(
        f'[game]\nversion = "42.22.2"\nbranch = "stable"\nbuildid = "{buildid}"\n'
        f'manifest_path = "{(root / "appmanifest_108600.acf").as_posix()}"\n')


def test_appmanifest(tmp_path):
    game_pins(tmp_path)
    acf(tmp_path, "26486631")
    assert check(tmp_path / "PINS.toml") == []
    acf(tmp_path, "26486631", beta="")
    assert check(tmp_path / "PINS.toml") == []
    acf(tmp_path, "26486631", beta="unstable")
    assert check(tmp_path / "PINS.toml")
    acf(tmp_path, "111")
    assert check(tmp_path / "PINS.toml")
    (tmp_path / "appmanifest_108600.acf").unlink()
    assert check(tmp_path / "PINS.toml")  # missing fails closed


# Test 3
def test_safe_extract(tmp_path):
    z = tmp_path / "evil.zip"
    with zipfile.ZipFile(z, "w") as zf:
        zf.writestr("../evil.txt", "x")
    with pytest.raises(ValueError):
        pins.safe_extract(z, tmp_path / "out")
    assert not (tmp_path / "evil.txt").exists()
    ok = tmp_path / "ok.zip"
    with zipfile.ZipFile(ok, "w") as zf:
        zf.writestr("d/f.txt", "x")
    pins.safe_extract(ok, tmp_path / "good")
    assert (tmp_path / "good/d/f.txt").read_text() == "x"
    with pytest.raises(ValueError):
        pins.safe_extract(ok, tmp_path / "good")  # non-empty


# Test 4
def test_tree_manifest(tmp_path):
    d = tmp_path / "t"
    write(d / "b.txt", b"2")
    write(d / "a/c.txt", b"1")
    m = pins.tree_manifest(d)
    assert m == f"a/c.txt {sha(b'1')}\nb.txt {sha(b'2')}\n"
    assert pins.tree_manifest(d) == m
    (tmp_path / "man").write_text(m)
    (tmp_path / "PINS.toml").write_text(f'[trees.t]\ndir = "t"\nmanifest = "man"\n')
    assert check(tmp_path / "PINS.toml") == []
    write(d / "new.txt", b"x")
    assert check(tmp_path / "PINS.toml")
    (d / "new.txt").unlink()
    (d / "b.txt").write_bytes(b"3")
    assert check(tmp_path / "PINS.toml")


# Test 5
def test_fetch(tmp_path):
    src = write(tmp_path / "src.bin", b"payload")
    url = src.as_uri()
    dest = tmp_path / "dl" / "x.bin"
    pins.fetch(url, dest, sha(b"payload"), md5=hashlib.md5(b"payload").hexdigest())
    assert dest.read_bytes() == b"payload" and not list(dest.parent.glob("*.part"))
    bad = tmp_path / "dl" / "y.bin"
    with pytest.raises(ValueError):
        pins.fetch(url, bad, "0" * 64)
    assert not bad.exists() and not list(bad.parent.glob("*.part"))
    with pytest.raises(ValueError):
        pins.fetch(url, bad, sha(b"payload"), md5="0" * 32)
    assert not bad.exists()


# Test 6
def tools_toml(tmp_path, active_extra="", fb_status="inactive", selected="user-decision-after-research"):
    a = write(tmp_path / "a.zip", b"A")
    b = write(tmp_path / "b.zip", b"B")
    (tmp_path / "PINS.toml").write_text(
        f'[tools.active]\nversion = "261030"\nzip = "a.zip"\nsha256 = "{sha(b"A")}"\nselected_by = "{selected}"\n'
        f'{active_extra}'
        f'[tools.fallback]\nversion = "260909"\nzip = "b.zip"\nsha256 = "{sha(b"B")}"\nstatus = "{fb_status}"\n')
    return tmp_path / "PINS.toml"


def test_tools_switch(tmp_path):
    assert check(tools_toml(tmp_path)) == []
    assert check(tools_toml(tmp_path, fb_status="active"))  # silent switch shape
    assert check(tools_toml(tmp_path, fb_status="phase2_target")) == []
    # user-approved-switch needs full approval incl. existing evidence
    assert check(tools_toml(tmp_path, selected="user-approved-switch"))
    write(tmp_path / "ev.md", "evidence")
    ap = '[tools.active.approval]\ndate = "2026-11-11"\nreason = "incompatible"\nevidence = "ev.md"\n'
    assert check(tools_toml(tmp_path, ap, "phase2_target", "user-approved-switch")) == []
    ap_missing = ap.replace("ev.md", "nope.md")
    assert check(tools_toml(tmp_path, ap_missing, "phase2_target", "user-approved-switch"))
    ap_empty = ap.replace('"incompatible"', '""')
    assert check(tools_toml(tmp_path, ap_empty, "phase2_target", "user-approved-switch"))
    assert check(tools_toml(tmp_path, selected="whatever"))


# Test 7
def venv_fixture(tmp_path, pkgs=(("foo", "1.0"), ("bar-baz", "2.1")), status="locked"):
    sp = tmp_path / "venv/Lib/site-packages"
    for n, v in pkgs:
        write(sp / f"{n.replace('-', '_')}-{v}.dist-info/METADATA", f"Metadata-Version: 2.1\nName: {n}\nVersion: {v}\n")
        write(sp / n.replace("-", "_") / "__init__.py", f"# {n}")
    write(sp / "foo/__pycache__/x.pyc", b"\0")
    write(tmp_path / "venv/Scripts/python.exe", b"")
    req = write(tmp_path / "reqs.txt", "# header\nfoo==1.0 --hash=sha256:" + "a" * 64 + "\nbar-baz==2.1 --hash=sha256:" + "b" * 64 + "\n")
    man = write(tmp_path / "venv.manifest", pins.tree_manifest(sp, skip_pyc=True))
    t = (f'[knoxmap_venv]\nstatus = "{status}"\n' if status == "pending" else
         f'[knoxmap_venv]\nstatus = "locked"\npython_version = "3.13"\nvenv_python = "venv/Scripts/python.exe"\n'
         f'requirements_file = "reqs.txt"\nrequirements_sha256 = "{sha(req.read_bytes())}"\n'
         f'site_packages_manifest = "venv.manifest"\n'
         f'site_packages_manifest_sha256 = "{sha(man.read_bytes())}"\nreviewed_by = "user"\nreviewed_date = "2026-11-11"\n')
    (tmp_path / "PINS.toml").write_text(t)
    return tmp_path / "PINS.toml", sp, req


def test_venv_lock(tmp_path):
    p, sp, req = venv_fixture(tmp_path)
    assert check(p) == []
    # extra package
    write(sp / "evil-9.9.dist-info/METADATA", "Name: evil\nVersion: 9.9\n")
    assert check(p)
    import shutil
    shutil.rmtree(sp / "evil-9.9.dist-info")
    assert check(p) == []
    # altered code file fails manifest hash
    write(sp / "foo/__init__.py", "# tampered")
    assert check(p)


def test_venv_missing_hash_and_missing_pkg(tmp_path):
    p, sp, req = venv_fixture(tmp_path)
    req.write_text(req.read_text().replace(" --hash=sha256:" + "a" * 64, ""))
    # requirements hash now differs too; rewrite pin to isolate the per-line rule
    p.write_text(p.read_text().replace(p.read_text().split('requirements_sha256 = "')[1][:64], sha(req.read_bytes())))
    assert any("--hash" in why for _, why in check(p))
    p2, sp2, req2 = venv_fixture(tmp_path / "m", pkgs=(("foo", "1.0"),))
    assert check(p2)  # bar-baz listed but not installed


def test_venv_pending(tmp_path):
    p, _, _ = venv_fixture(tmp_path, status="pending")
    assert check(p)
    assert check(p, allow_pending_venv=True) == []


def test_python_and_lock(tmp_path):
    lock = write(tmp_path / "requirements.lock", "x==1\n")
    (tmp_path / "PINS.toml").write_text(
        f'[python]\nversion = "{platform.python_version()}"\nrequirements_lock = "requirements.lock"\n'
        f'requirements_lock_sha256 = "{sha(lock.read_bytes())}"\n')
    assert check(tmp_path / "PINS.toml") == []
    lock.write_text("x==2\n")
    assert check(tmp_path / "PINS.toml")
