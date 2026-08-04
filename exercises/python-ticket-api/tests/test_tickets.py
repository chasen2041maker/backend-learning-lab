from __future__ import annotations

from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.repository import InMemoryTicketRepository


async def test_create_get_and_close_ticket() -> None:
    app = create_app(InMemoryTicketRepository())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        created = await client.post(
            "/api/v1/tickets",
            headers={"x-request-id": "req_test_create"},
            json={"tenant_id": "tenant_a", "title": "Cannot sign in"},
        )
        assert created.status_code == 201
        assert created.headers["x-request-id"] == "req_test_create"
        ticket = created.json()["data"]
        assert ticket["status"] == "open"
        assert ticket["version"] == 1

        fetched = await client.get(
            f"/api/v1/tickets/{ticket['id']}", params={"tenant_id": "tenant_a"}
        )
        assert fetched.status_code == 200
        assert fetched.json()["data"]["title"] == "Cannot sign in"

        closed = await client.post(
            f"/api/v1/tickets/{ticket['id']}/close",
            json={"tenant_id": "tenant_a", "expected_version": 1},
        )
        assert closed.status_code == 200
        assert closed.json()["data"]["status"] == "closed"
        assert closed.json()["data"]["version"] == 2


async def test_cross_tenant_read_is_hidden_as_not_found() -> None:
    app = create_app(InMemoryTicketRepository())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        created = await client.post(
            "/api/v1/tickets", json={"tenant_id": "tenant_a", "title": "Private ticket"}
        )
        ticket_id = created.json()["data"]["id"]

        response = await client.get(
            f"/api/v1/tickets/{ticket_id}", params={"tenant_id": "tenant_b"}
        )
        assert response.status_code == 404
        assert response.json()["code"] == "ticket_not_found"


async def test_optimistic_version_conflict() -> None:
    app = create_app(InMemoryTicketRepository())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        created = await client.post(
            "/api/v1/tickets", json={"tenant_id": "tenant_a", "title": "Versioned"}
        )
        ticket_id = created.json()["data"]["id"]

        response = await client.post(
            f"/api/v1/tickets/{ticket_id}/close",
            json={"tenant_id": "tenant_a", "expected_version": 99},
        )
        assert response.status_code == 409
        assert response.json()["code"] == "ticket_version_conflict"


async def test_validation_rejects_blank_title() -> None:
    app = create_app(InMemoryTicketRepository())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/tickets", json={"tenant_id": "tenant_a", "title": "   "}
        )
        assert response.status_code == 422
        assert response.json()["code"] == "invalid_ticket_input"
        assert response.json()["request_id"].startswith("req_")
