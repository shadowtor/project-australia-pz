import argparse
import importlib
import pathlib
import shutil
import sys

from pa import compose, gates, pins, release

NAMES = ("pins", "build", "compose", "gates", "release", "stats", "decision", "ledger", "edits")


def register_all(subparsers, names=NAMES):
    """Let later plans add subcommands via pa.<name>.register(subparsers) without editing this file."""
    for n in names:
        try:
            mod = importlib.import_module(f"pa.{n}")
        except ModuleNotFoundError as e:
            if e.name == f"pa.{n}":
                continue  # module not written yet
            raise  # broken plan module (e.g. missing third-party import) must not be hidden
        if hasattr(mod, "register"):
            mod.register(subparsers)


def tracer(args):
    fx, work = pathlib.Path(args.fixture), pathlib.Path(args.work)
    bad = pins.verify(fx / "PINS.toml")
    if bad:
        for rel, why in bad:
            print(f"PINS FAIL {rel}: {why}")
        return 1
    gen = work / "generated"  # stand-in for KnoxMap generation (plan 06)
    if gen.exists():
        shutil.rmtree(gen)
    shutil.copytree(fx / "generated", gen)
    composed = compose.compose(gen, fx / "edits", work / "composed")
    findings = gates.palette_gate(fx / "map.bmp", gates.load_palette(fx / "palette.txt"))
    gates.report(findings, "palette", work / "reports")
    if findings:
        return 1
    print("RELEASE", release.release(composed, work))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="pa")
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("tracer", help="thin end-to-end slice on a fixture world")
    t.add_argument("--fixture", required=True)
    t.add_argument("--work", required=True)
    t.set_defaults(func=tracer)
    register_all(sub)
    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
