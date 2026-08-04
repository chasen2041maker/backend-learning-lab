from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).parents[1]
LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


def main() -> None:
    broken: list[str] = []
    for document in ROOT.rglob("*.md"):
        if any(part in {".git", ".venv"} for part in document.parts):
            continue
        for target in LINK.findall(document.read_text(encoding="utf-8")):
            target = target.strip().strip("<>")
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            path_text = unquote(target.split("#", 1)[0])
            if not path_text:
                continue
            resolved = (document.parent / path_text).resolve()
            if not resolved.exists():
                broken.append(f"{document.relative_to(ROOT)} -> {target}")
    if broken:
        raise SystemExit("broken Markdown links:\n" + "\n".join(broken))
    print("local Markdown links valid")


if __name__ == "__main__":
    main()
