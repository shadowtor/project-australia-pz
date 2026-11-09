import hashlib
import os
import pathlib
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
