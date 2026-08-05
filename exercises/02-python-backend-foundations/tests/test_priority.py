from __future__ import annotations

import sys
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).parents[1]))

from starter.api import app
from starter.models import ApiResponse, TicketCreate
from starter.repository import InMemoryTicketRepository
from starter.service import TicketService


@pytest.mark.asyncio
async def test_new_ticket_defaults_to_normal_priority() -> None:
    service = TicketService(InMemoryTicketRepository())

    ticket = await service.create("tenant_a", TicketCreate(title="Cannot sign in"))

    assert ticket.priority == "normal"


@pytest.mark.asyncio
@pytest.mark.parametrize("priority", ["low", "normal", "high"])
async def test_supported_priority_is_preserved(priority: str) -> None:
    service = TicketService(InMemoryTicketRepository())

    ticket = await service.create(
        "tenant_a", TicketCreate(title="Cannot sign in", priority=priority)
    )

    assert ticket.priority == priority


def test_invalid_priority_is_rejected_before_service_call() -> None:
    with pytest.raises(ValidationError):
        TicketCreate(title="Cannot sign in", priority="urgent")


@pytest.mark.asyncio
async def test_invalid_priority_returns_http_422() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/tickets",
            json={"title": "Cannot sign in", "priority": "urgent"},
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_api_response_contains_priority() -> None:
    service = TicketService(InMemoryTicketRepository())
    ticket = await service.create("tenant_a", TicketCreate(title="Cannot sign in"))

    response = ApiResponse(
        code="ok",
        message="created",
        request_id="req_lesson_002",
        data=ticket,
    )

    assert response.model_dump(mode="json")["data"]["priority"] == "normal"
