from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).parents[1]
SKIP_PARTS = {".git", ".venv", "__pycache__"}
PATTERNS = {
    "private key": re.compile("BEGIN" + r" [A-Z ]*PRIVATE KEY"),
    "AWS access key": re.compile("AKIA" + r"[0-9A-Z]{16}"),
    "GitHub token": re.compile("gh" + r"[pousr]_[A-Za-z0-9]{30,}"),
    "Slack token": re.compile("xox" + r"[abprs]-[A-Za-z0-9-]{20,}"),
    "company workspace path": re.compile(r"(?i)[A-Z]:[\\/]company[\\/]"),
    "user profile path": re.compile(r"(?i)[A-Z]:[\\/]Users[\\/][^\\/]+[\\/]"),
}


def main() -> None:
    findings: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.stat().st_size > 1_000_000:
            continue
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        raw = path.read_bytes()
        if b"\x00" in raw:
            continue
        content = raw.decode("utf-8", errors="replace")
        for name, pattern in PATTERNS.items():
            if pattern.search(content):
                findings.append(f"{path.relative_to(ROOT)}: {name}")
    if findings:
        raise SystemExit("possible secrets/private data:\n" + "\n".join(findings))
    print("secret/private-data patterns not found")


if __name__ == "__main__":
    main()
