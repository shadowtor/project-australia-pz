"""Hand-build the proxy_tools 0.1.0 wheel from its hash-verified sdist (user-approved, T-01-SC).

proxy_tools publishes only an sdist; building it normally runs setup.py. Instead this copies the one
module out of the sdist (never executed) into a pure-Python wheel. Deterministic: fixed timestamps,
sorted entries. stdlib only. Usage: python -I tools/make_proxy_tools_wheel.py SDIST OUT_DIR
"""
import base64
import hashlib
import pathlib
import sys
import tarfile
import zipfile

SDIST_SHA256 = "ccb3751f529c047e2d8a58440d86b205303cf0fe8146f784d1cbcd94f0a28010"
MEMBER = "proxy_tools-0.1.0/proxy_tools/__init__.py"
DI = "proxy_tools-0.1.0.dist-info"
FILES = {
    f"{DI}/METADATA": (
        "Metadata-Version: 2.1\nName: proxy_tools\nVersion: 0.1.0\nSummary: Proxy Implementation\n"
        "Home-page: http://github.com/jtushman/proxy_tools\nAuthor: Jonathan Tushman\nLicense: MIT\n"
    ),
    f"{DI}/WHEEL": "Wheel-Version: 1.0\nGenerator: hand-built-from-sdist\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
    f"{DI}/top_level.txt": "proxy_tools\n",
}


def build(sdist, out_dir):
    raw = pathlib.Path(sdist).read_bytes()
    if hashlib.sha256(raw).hexdigest() != SDIST_SHA256:
        raise SystemExit("sdist sha256 mismatch")
    with tarfile.open(sdist) as t:
        m = t.getmember(MEMBER)  # exact fixed member name: no traversal possible
        if not m.isfile():
            raise SystemExit("unexpected member type")
        init = t.extractfile(m).read()
    entries = {"proxy_tools/__init__.py": init}
    entries.update({k: v.encode() for k, v in FILES.items()})
    rec = "".join(
        f"{n},sha256={base64.urlsafe_b64encode(hashlib.sha256(b).digest()).rstrip(b'=').decode()},{len(b)}\n"
        for n, b in sorted(entries.items())
    ) + f"{DI}/RECORD,,\n"
    entries[f"{DI}/RECORD"] = rec.encode()
    out = pathlib.Path(out_dir) / "proxy_tools-0.1.0-py3-none-any.whl"
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for n in sorted(entries):
            zi = zipfile.ZipInfo(n, (1980, 1, 1, 0, 0, 0))
            zi.external_attr = 0o644 << 16
            zi.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(zi, entries[n])
    print(out, hashlib.sha256(out.read_bytes()).hexdigest())


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
