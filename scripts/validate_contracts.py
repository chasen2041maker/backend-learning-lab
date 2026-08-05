from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parents[1]


def load(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def main() -> None:
    http = load("contracts/http-cases.json")
    assert http["contract_version"] == 1
    assert http["id_format"] == "uuid-v4"
    assert http["title_length_unit"] == "unicode_code_points"
    cases = http["create_cases"]
    names = [case["name"] for case in cases]
    assert names and len(names) == len(set(names)), "contract case names must be unique"
    for case in cases:
        assert isinstance(case["authorization"], bool)
        assert case["expected_status"] in {201, 400, 401, 422}
        assert case["expected_code"]
        assert ("body" in case) ^ ("raw_body" in case) ^ ("repeat_title" in case)

    endpoint_cases = {
        "health_cases": {200},
        "get_cases": {200, 404, 422},
        "list_cases": {200, 422},
        "close_cases": {200, 404, 409, 422},
    }
    for field, allowed_statuses in endpoint_cases.items():
        endpoint = http.get(field)
        assert isinstance(endpoint, list) and endpoint, f"{field} must not be empty"
        names = [case["name"] for case in endpoint]
        assert len(names) == len(set(names)), f"{field} case names must be unique"
        for case in endpoint:
            assert isinstance(case["authorization"], bool)
            assert case["expected_status"] in allowed_statuses
            if field == "health_cases":
                assert case["expected_body"] == {"status": "ok"}
            elif field in {"get_cases", "close_cases"}:
                assert case.get("ticket_id") or case.get("seed_title")
                assert case["expected_code"]
            else:
                assert case["expected_code"]

    event = load("contracts/event.schema.json")
    required = set(event["required"])
    expected = {
        "event_id",
        "event_type",
        "event_version",
        "occurred_at",
        "tenant_id",
        "request_id",
        "trace_id",
        "payload",
    }
    assert required == expected, f"event envelope fields drifted: {required ^ expected}"
    assert expected <= set(event["properties"])
    assert event["properties"]["event_id"]["format"] == "uuid"
    assert event["properties"]["occurred_at"]["format"] == "date-time"
    assert event["properties"]["payload"]["type"] == "object"
    print(f"contracts valid: {len(cases)} HTTP cases, {len(required)} event fields")


if __name__ == "__main__":
    main()
