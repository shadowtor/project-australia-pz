import pathlib
import sys

r = pathlib.Path(sys.argv[1]) / "config" / "Rules.txt"
r.write_text(r.read_text(encoding="utf-8") + "# trees\n" + ("KnoxMap road Yard bed_soil\n" if "trees" == "roads" else ""), encoding="utf-8")
