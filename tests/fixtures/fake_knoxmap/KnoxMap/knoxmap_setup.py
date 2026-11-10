def patch_rules(tools):
    raise AssertionError("wrapper must stub patch_rules (it spawns a bare sys.executable)")


def configure_tools(tools, game):
    (tools / "settings").mkdir(exist_ok=True)
    (tools / "settings" / "PZTools.ini").write_text(f"[Paths]\nTilesDirectory={tools.as_posix()}/Tiles\n", encoding="utf-8")
    d = tools / "Tiles" / "2x"
    d.mkdir(parents=True, exist_ok=True)
    (d / "sheet_01.png").write_bytes(b"png")
    patch_rules(tools)
