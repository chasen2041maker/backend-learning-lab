from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1]))

from starter.repository import InMemoryTicketRepository
from starter.service import (
    TicketNotFound,
    TicketService,
    TicketStateConflict,
    TicketVersionConflict,
)


@pytest.mark.asyncio
async def test_close_moves_open_ticket_to_closed() -> None:
    service = TicketService(InMemoryTicketRepository())

    ticket = await service.close("tenant_a", "ticket-1", expected_version=1)

    assert ticket == {
        "tenant_id": "tenant_a",
        "status": "closed",
        "version": 2,
    }


@pytest.mark.asyncio
async def test_missing_ticket_is_a_domain_error() -> None:
    service = TicketService(InMemoryTicketRepository())

    with pytest.raises(TicketNotFound):
        await service.close("tenant_a", "missing", expected_version=1)


@pytest.mark.asyncio
async def test_stale_version_is_rejected() -> None:
    service = TicketService(InMemoryTicketRepository())

    with pytest.raises(TicketVersionConflict):
        await service.close("tenant_a", "ticket-1", expected_version=99)


@pytest.mark.asyncio
async def test_duplicate_close_is_rejected() -> None:
    service = TicketService(InMemoryTicketRepository())
    await service.close("tenant_a", "ticket-1", expected_version=1)

    with pytest.raises(TicketStateConflict):
        await service.close("tenant_a", "ticket-1", expected_version=99)


@pytest.mark.asyncio
async def test_cross_tenant_ticket_is_hidden_as_not_found() -> None:
    service = TicketService(InMemoryTicketRepository())

    with pytest.raises(TicketNotFound):
        await service.close("tenant_b", "ticket-1", expected_version=1)
