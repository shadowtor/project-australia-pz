import hashlib
import pathlib
import tomllib


def verify(pins_path):
    """Return list of (relpath, reason) mismatches for [files] in PINS.toml. Fail closed: missing = mismatch."""
    pins_path = pathlib.Path(pins_path)
    pins = tomllib.loads(pins_path.read_text(encoding="utf-8")).get("files", {})
    bad = []
    for rel, want in pins.items():
        p = pins_path.parent / rel
        if not p.is_file():
            bad.append((rel, "missing"))
        elif hashlib.sha256(p.read_bytes()).hexdigest() != want:
            bad.append((rel, "sha256 mismatch"))
    return bad
