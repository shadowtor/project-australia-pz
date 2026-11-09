import os
import pathlib


def main(argv):
    d = pathlib.Path(argv[0])
    (d / f"{d.name}.tbx").write_text("tbx", encoding="utf-8")
    (d / "build.json").write_text("{}", encoding="utf-8")
    return 0
