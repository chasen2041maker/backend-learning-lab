from __future__ import annotations

import json
from pathlib import Path


def load_http_cases(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def cases_with_expected_code(
    contract: dict[str, object], section: str, expected_code: str
) -> list[str]:
    """Return matching case names from one contract section.

    TODO: validate that the section is a list, then select case names whose
    expected_code matches exactly.
    """
    raise NotImplementedError
