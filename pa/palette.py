"""Rules.txt parser: palette colours come from the pinned tools' config/Rules.txt at runtime (D-10), never Knoxify files."""
import pathlib
import re

_RULE = re.compile(r"\brule\s*\{(.*?)\}", re.S)
_LABEL = re.compile(r'^\s*label\s*=\s*"?([^"\n]*?)"?\s*$', re.M)
_COLOR = re.compile(r"^\s*color\s*=(.*)$", re.M)


def parse_rules(path):
    """-> {label: (r, g, b)}. Rules without a colour are skipped; a malformed colour line raises ValueError."""
    text = pathlib.Path(path).read_text(encoding="utf-8", errors="replace")
    text = re.sub(r"(//|#).*", "", text)
    out = {}
    for body in _RULE.findall(text):
        c = _COLOR.search(body)
        if not c:
            continue
        label = _LABEL.search(body)
        parts = c.group(1).split()
        if not label or len(parts) != 3 or not all(p.isdigit() and int(p) < 256 for p in parts):
            raise ValueError(f"malformed rule colour line: color ={c.group(1)}")
        out[label.group(1)] = tuple(int(p) for p in parts)
    return out
