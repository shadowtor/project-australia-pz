"""BUILD-04: failed generate/compile/gate never touches current.txt or the last release; install is atomic."""
import hashlib
import pathlib
import shutil
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pa import release  # noqa: E402

PAYLOAD = ROOT / "tests" / "fixtures" / "release" / "payload"


def tree_hash(d):
    h = hashlib.sha256()
    for p in sorted(pathlib.Path(d).rglob("*")):
        if p.is_file():
            h.update(p.relative_to(d).as_posix().encode() + b"\0" + p.read_bytes())
    return h.hexdigest()


def put(staging):
    (staging / "f.txt").write_text("data", encoding="utf-8")


def noop(_s):
    pass


@pytest.fixture
def store(tmp_path):
    release.build_release(put, noop, [], tmp_path, "v1")
    return tmp_path


def snapshot(root):
    return (root / "current.txt").read_bytes(), tree_hash(root / "releases" / "v1")


def test_generate_failure_keeps_v1(store):
    before = snapshot(store)

    def boom(_s):
        (_s / "partial.txt").write_text("x")
        raise RuntimeError("generate died")

    with pytest.raises(RuntimeError):
        release.build_release(boom, noop, [], store, "v2")
    assert snapshot(store) == before
    assert not (store / "releases" / "v2").exists()
    assert (store / "staging-failed" / "v2" / "partial.txt").exists()


def test_compile_failure_keeps_v1(store):
    before = snapshot(store)

    def bad_compile(_s):
        subprocess.run([sys.executable, "-c", "raise SystemExit(3)"], check=True)

    with pytest.raises(subprocess.CalledProcessError):
        release.build_release(put, bad_compile, [], store, "v2")
    assert snapshot(store) == before
    assert not (store / "releases" / "v2").exists()


def test_gate_failure_quarantines(store):
    before = snapshot(store)
    with pytest.raises(release.ReleaseError):
        release.build_release(put, noop, [lambda _s: ["bad pixel"]], store, "v2")
    assert snapshot(store) == before
    assert (store / "staging-failed" / "v2" / "f.txt").exists()
    assert not (store / "staging" / "v2").exists()
    assert not (store / "releases" / "v2").exists()


def test_success_promotes(store):
    release.build_release(put, noop, [], store, "v2")
    assert (store / "releases" / "v2" / "f.txt").exists()
    assert (store / "current.txt").read_text().strip() == "v2"
    assert not (store / "current.txt.tmp").exists()
    assert (store / "releases" / "v1").exists()


def test_existing_release_is_immutable(store):
    before = snapshot(store)
    with pytest.raises(release.ReleaseError):
        release.build_release(put, noop, [], store, "v1")
    assert snapshot(store) == before


@pytest.mark.parametrize("bad", ["../x", "a/b", "a\b", "", "..", "v1/..", "C:evil", ".hidden"])
def test_version_and_current_traversal_rejected(store, bad):
    with pytest.raises(release.ReleaseError):
        release.build_release(put, noop, [], store, bad)
    (store / "current.txt").write_text(bad + "\n")
    with pytest.raises(release.ReleaseError):
        release.install(store, store / "mods", "m")


def test_install_swaps_and_survives_copy_failure(store, tmp_path, monkeypatch):
    mods = tmp_path / "mods"
    release.install(store, mods, "pa")
    assert (mods / "pa" / "f.txt").read_text() == "data"
    release.build_release(lambda s: (s / "f.txt").write_text("v2data"), noop, [], store, "v2")
    release.install(store, mods, "pa")
    assert (mods / "pa" / "f.txt").read_text() == "v2data"
    assert sorted(p.name for p in mods.iterdir()) == ["pa"]
    before = tree_hash(mods / "pa")

    def broken(*a, **k):
        raise OSError("disk full")

    monkeypatch.setattr(release.shutil, "copytree", broken)
    with pytest.raises(OSError):
        release.install(store, mods, "pa")
    assert tree_hash(mods / "pa") == before
    assert not (mods / "pa.new").exists()


def pa(*args):
    return subprocess.run([sys.executable, "-m", "pa", *args], cwd=ROOT, capture_output=True, text=True)


def test_cli_release_from_payload(tmp_path):
    payload_before = tree_hash(PAYLOAD)
    r = pa("release", "--payload", str(PAYLOAD), "--version", "v2", "--root", str(tmp_path))
    assert r.returncode == 0, r.stdout + r.stderr
    assert (tmp_path / "current.txt").read_text().strip() == "v2"
    assert (tmp_path / "releases" / "v2" / "ATTRIBUTION.txt").exists()
    assert tree_hash(PAYLOAD) == payload_before


def test_cli_missing_or_empty_payload_fails(tmp_path):
    root = tmp_path / "r"
    release.build_release(put, noop, [], root, "v1")
    empty = tmp_path / "empty"
    empty.mkdir()
    for p in (tmp_path / "nope", empty):
        r = pa("release", "--payload", str(p), "--version", "v2", "--root", str(root))
        assert r.returncode != 0
        assert (root / "current.txt").read_text().strip() == "v1"
        assert not (root / "releases" / "v2").exists()


def test_cli_gate_failure_quarantines(tmp_path):
    from PIL import Image
    world = tmp_path / "world"
    world.mkdir()
    Image.new("RGB", (4, 4), (250, 0, 250)).save(world / "map.bmp")
    (world / "palette.txt").write_text("10 20 30\n")
    cfg = tmp_path / "gates.yaml"
    cfg.write_text("palette: {bmp: map.bmp, palette: palette.txt}\n")
    root = tmp_path / "r"
    r = pa("release", "--payload", str(PAYLOAD), "--version", "v2", "--root", str(root),
           "--world", str(world), "--gates-config", str(cfg))
    assert r.returncode != 0
    assert (root / "staging-failed" / "v2").is_dir()
    assert not (root / "releases" / "v2").exists()
    assert not (root / "current.txt").exists()


def test_cli_gates_config_cannot_escape_world(tmp_path):
    world = tmp_path / "world"
    world.mkdir()
    cfg = tmp_path / "gates.yaml"
    cfg.write_text("palette: {bmp: ../x.bmp, palette: ../p.txt}\n")
    r = pa("release", "--payload", str(PAYLOAD), "--version", "v2", "--root", str(tmp_path / "r"),
           "--world", str(world), "--gates-config", str(cfg))
    assert r.returncode != 0
    assert not (tmp_path / "r" / "current.txt").exists()
