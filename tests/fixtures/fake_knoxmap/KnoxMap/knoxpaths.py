import pathlib


def pz_install_from(p):
    return pathlib.Path(p) if pathlib.Path(p).is_dir() else None
