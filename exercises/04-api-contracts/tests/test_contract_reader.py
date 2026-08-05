from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from starter.contract_reader import cases_with_expected_code, load_http_cases

CONTRACT = Path(__file__).parents[3] / "contracts" / "http-cases.json"


def test_contract_declares_strict_input_cases() -> None:
    contract = load_http_cases(CONTRACT)

    names = cases_with_expected_code(contract, "create_cases", "invalid_ticket_input")

    assert "unknown field" in names
    assert "client tenant forgery" in names
    assert "numeric title" in names


def test_contract_declares_hidden_cross_tenant_read() -> None:
    contract = load_http_cases(CONTRACT)

    names = cases_with_expected_code(contract, "get_cases", "ticket_not_found")

    assert "cross tenant ticket is hidden" in names


def test_contract_distinguishes_invalid_json() -> None:
    contract = load_http_cases(CONTRACT)

    names = cases_with_expected_code(contract, "create_cases", "invalid_json")

    assert names == ["empty body", "malformed json", "trailing json"]
