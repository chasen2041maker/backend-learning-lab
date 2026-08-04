from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .errors import (
    DomainError,
    TicketNotFound,
    TicketStateConflict,
    TicketVersionConflict,
)
from .models import ApiResponse, Ticket, TicketClose, TicketCreate
from .repository import InMemoryTicketRepository, TicketRepository
from .service import TicketService

logger = logging.getLogger("ticket_api")


def create_app(repository: TicketRepository | None = None) -> FastAPI:
    app = FastAPI(title="Backend Learning Lab Ticket API", version="0.1.0")
    repo = repository or InMemoryTicketRepository()
    service = TicketService(repo)

    def get_service() -> TicketService:
        return service

    @app.middleware("http")
    async def request_context(
        request: Request,
        call_next: Callable[[Request], Awaitable[JSONResponse]],
    ):
        request_id = request.headers.get("x-request-id") or f"req_{uuid4().hex}"
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        return response

    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
        status_code = 409
        if isinstance(exc, TicketNotFound):
            status_code = 404
        elif isinstance(exc, (TicketStateConflict, TicketVersionConflict)):
            status_code = 409
        return JSONResponse(
            status_code=status_code,
            content={
                "code": exc.code,
                "message": str(exc),
                "request_id": request.state.request_id,
                "data": None,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "code": "invalid_ticket_input",
                "message": "request validation failed",
                "request_id": request.state.request_id,
                "data": {"errors": jsonable_encoder(exc.errors())},
            },
        )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/v1/tickets", status_code=201, response_model=ApiResponse)
    async def create_ticket(
        command: TicketCreate,
        request: Request,
        ticket_service: TicketService = Depends(get_service),
    ) -> ApiResponse:
        ticket = await ticket_service.create(command)
        logger.info("ticket_created", extra={"ticket_id": str(ticket.id)})
        return ApiResponse(
            code="ok",
            message="created",
            request_id=request.state.request_id,
            data=ticket.model_dump(mode="json"),
        )

    @app.get("/api/v1/tickets/{ticket_id}", response_model=ApiResponse)
    async def get_ticket(
        ticket_id: UUID,
        request: Request,
        tenant_id: str = Query(min_length=1, max_length=64),
        ticket_service: TicketService = Depends(get_service),
    ) -> ApiResponse:
        ticket = await ticket_service.get(ticket_id, tenant_id)
        return _success(request, ticket)

    @app.get("/api/v1/tickets", response_model=ApiResponse)
    async def list_tickets(
        request: Request,
        tenant_id: str = Query(min_length=1, max_length=64),
        ticket_service: TicketService = Depends(get_service),
    ) -> ApiResponse:
        tickets = await ticket_service.list_for_tenant(tenant_id)
        return ApiResponse(
            code="ok",
            message="ok",
            request_id=request.state.request_id,
            data=[ticket.model_dump(mode="json") for ticket in tickets],
        )

    @app.post("/api/v1/tickets/{ticket_id}/close", response_model=ApiResponse)
    async def close_ticket(
        ticket_id: UUID,
        command: TicketClose,
        request: Request,
        ticket_service: TicketService = Depends(get_service),
    ) -> ApiResponse:
        ticket = await ticket_service.close(
            ticket_id=ticket_id,
            tenant_id=command.tenant_id,
            expected_version=command.expected_version,
        )
        return _success(request, ticket)

    return app


def _success(request: Request, ticket: Ticket) -> ApiResponse:
    return ApiResponse(
        code="ok",
        message="ok",
        request_id=request.state.request_id,
        data=ticket.model_dump(mode="json"),
    )


app = create_app()
