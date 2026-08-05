from __future__ import annotations

from fastapi import FastAPI

from .models import ApiResponse, Ticket, TicketCreate
from .repository import InMemoryTicketRepository
from .service import TicketService

app = FastAPI()
service = TicketService(InMemoryTicketRepository())


@app.post("/api/v1/tickets", status_code=201, response_model=ApiResponse[Ticket])
async def create_ticket(command: TicketCreate) -> ApiResponse[Ticket]:
    ticket = await service.create("tenant_a", command)
    return ApiResponse(
        code="ok",
        message="created",
        request_id="req_lesson_002",
        data=ticket,
    )
