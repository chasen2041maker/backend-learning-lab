from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.models import Ticket
from app.repository import InMemoryTicketRepository

TOKEN_A = {"Authorization": "Bearer lab-token-tenant-a"}
TOKEN_B = {"Authorization": "Bearer lab-token-tenant-b"}
CONTRACT_PATH = Path(__file__).parents[3] / "contracts" / "http-cases.json"


class ExplodingRepository(InMemoryTicketRepository):
    async def create(self, ticket: Ticket) -> Ticket:
        raise RuntimeError("database unavailable")


async def test_create_get_and_close_ticket() -> None:
    app = create_app(InMemoryTicketRepository())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        created = await client.post(
            "/api/v1/tickets",
            headers={**TOKEN_A, "x-request-id": "req_test_create"},
            json={"title": "Cannot sign in"},
        )
        assert created.status_code == 201
        assert created.headers["x-request-id"] == "req_test_create"
        ticket = created.json()["data"]
        assert ticket["status"] == "open"
        assert ticket["version"] == 1

        fetched = await client.get(f"/api/v1/tickets/{ticket['id']}", headers=TOKEN_A)
        assert fetched.status_code == 200
        assert fetched.json()["data"]["title"] == "Cannot sign in"

        closed = await client.post(
            f"/api/v1/tickets/{ticket['id']}/close",
            headers=TOKEN_A,
            json={"expected_version": 1},
        )
        assert closed.status_code == 200
        assert closed.json()["data"]["status"] == "closed"
        assert closed.json()["data"]["version"] == 2


async def test_cross_tenant_read_is_hidden_as_not_found() -> None:
    app = create_app(InMemoryTicketRepository())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        created = await client.post(
            "/api/v1/tickets", headers=TOKEN_A, json={"title": "Private ticket"}
        )
        ticket_id = created.json()["data"]["id"]

        response = await client.get(f"/api/v1/tickets/{ticket_id}", headers=TOKEN_B)
        assert response.status_code == 404
        assert response.json()["code"] == "ticket_not_found"


async def test_optimistic_version_conflict() -> None:
    app = create_app(InMemoryTicketRepository())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        created = await client.post("/api/v1/tickets", headers=TOKEN_A, json={"title": "Versioned"})
        ticket_id = created.json()["data"]["id"]

        response = await client.post(
            f"/api/v1/tickets/{ticket_id}/close",
            headers=TOKEN_A,
            json={"expected_version": 99},
        )
        assert response.status_code == 409
        assert response.json()["code"] == "ticket_version_conflict"


async def test_validation_rejects_blank_title() -> None:
    app = create_app(InMemoryTicketRepository())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/tickets", headers=TOKEN_A, json={"title": "   "})
        assert response.status_code == 422
        assert response.json()["code"] == "invalid_ticket_input"
        assert response.json()["request_id"].startswith("req_")


async def test_authentication_and_client_tenant_forgery_are_rejected() -> None:
    app = create_app(InMemoryTicketRepository())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        missing_auth = await client.post("/api/v1/tickets", json={"title": "No auth"})
        assert missing_auth.status_code == 401
        assert missing_auth.json()["code"] == "authentication_required"

        forged_tenant = await client.post(
            "/api/v1/tickets",
            headers=TOKEN_A,
            json={"title": "Forged", "tenant_id": "tenant_b"},
        )
        assert forged_tenant.status_code == 422
        assert forged_tenant.json()["code"] == "invalid_ticket_input"


async def test_contract_rejects_unknown_fields_and_accepts_unicode_length() -> None:
    app = create_app(InMemoryTicketRepository())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        unknown = await client.post(
            "/api/v1/tickets", headers=TOKEN_A, json={"title": "Valid", "extra": True}
        )
        assert unknown.status_code == 422
        assert unknown.json()["code"] == "invalid_ticket_input"

        unicode_title = await client.post(
            "/api/v1/tickets", headers=TOKEN_A, json={"title": "中" * 100}
        )
        assert unicode_title.status_code == 201


async def test_unexpected_error_keeps_json_envelope_request_id_and_log(caplog) -> None:
    app = create_app(ExplodingRepository())
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/tickets",
            headers={**TOKEN_A, "X-Request-ID": "req_unexpected"},
            json={"title": "Explode"},
        )
    assert response.status_code == 500
    assert response.headers["X-Request-ID"] == "req_unexpected"
    assert response.json() == {
        "code": "internal_error",
        "message": "internal error",
        "request_id": "req_unexpected",
        "data": None,
    }
    assert any(getattr(record, "request_id", None) == "req_unexpected" for record in caplog.records)


async def test_list_uses_authenticated_tenant() -> None:
    app = create_app(InMemoryTicketRepository())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/api/v1/tickets", headers=TOKEN_A, json={"title": "A"})
        await client.post("/api/v1/tickets", headers=TOKEN_B, json={"title": "B"})
        response = await client.get("/api/v1/tickets", headers=TOKEN_A)
        assert response.status_code == 200
        assert [ticket["title"] for ticket in response.json()["data"]] == ["A"]


async def test_shared_create_contract_cases() -> None:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    app = create_app(InMemoryTicketRepository())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        for case in contract["create_cases"]:
            headers = TOKEN_A if case["authorization"] else {}
            if "raw_body" in case:
                response = await client.post(
                    "/api/v1/tickets",
                    headers={**headers, "Content-Type": "application/json"},
                    content=case["raw_body"],
                )
            else:
                body = case.get("body")
                if repeat := case.get("repeat_title"):
                    body = {"title": repeat["text"] * repeat["count"]}
                response = await client.post("/api/v1/tickets", headers=headers, json=body)

            assert response.status_code == case["expected_status"], case["name"]
            envelope = response.json()
            assert envelope["code"] == case["expected_code"], case["name"]
            if response.status_code == 201:
                ticket_id = UUID(envelope["data"]["id"])
                assert ticket_id.version == 4, case["name"]
