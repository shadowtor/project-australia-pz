import pathlib
import shutil


def main(argv):
    proj, name, mid, mods = pathlib.Path(argv[0]), argv[2], argv[4], pathlib.Path(argv[6])
    maps = mods / mid / "common" / "media" / "maps" / name
    maps.mkdir(parents=True, exist_ok=True)
    (mods / mid / "mod.info").write_text(f"name={name}\nid={mid}\n", encoding="utf-8")
    lots = proj / "lots"
    for f in (lots.iterdir() if lots.is_dir() else []):
        shutil.copy2(f, maps / f.name)
    return 0
