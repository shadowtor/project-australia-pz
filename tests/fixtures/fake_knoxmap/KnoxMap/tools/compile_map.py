import pathlib


def compile_map(project_dir, batch=4, exe=None, only_cells=None, backend=None, **kw):
    if only_cells and any(c[0] >= 99 for c in only_cells):
        raise RuntimeError("forced compile failure")
    lots = pathlib.Path(project_dir) / "lots"
    lots.mkdir(exist_ok=True)
    (lots / "world_0_0.lotpack").write_bytes(b"lot")
    (lots / "0_0.lotheader").write_bytes(b"hdr")
    (lots / "chunkdata_0_0.bin").write_bytes(b"chunk")
    return 1
