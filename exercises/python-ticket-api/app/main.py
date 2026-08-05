from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .errors import (
    AuthenticationRequired,
    DomainError,
    TicketNotFound,
    TicketStateConflict,
    TicketVersionConflict,
)
from .models import ApiResponse, Principal, Ticket, TicketClose, TicketCreate, TicketID
from .repository import InMemoryTicketRepository, TicketRepository
from .service import TicketService

logger = logging.getLogger("ticket_api")

LAB_TOKENS = {
    "lab-token-tenant-a": Principal(subject="user_a", tenant_id="tenant_a"),
    "lab-token-tenant-b": Principal(subject="user_b", tenant_id="tenant_b"),
}


def get_principal(authorization: str | None = Header(default=None)) -> Principal:
    """Learning-only token verifier; a real service verifies signed/opaque credentials."""
    if authorization is None or not authorization.startswith("Bearer "):
        raise AuthenticationRequired("a bearer token is required")
    principal = LAB_TOKENS.get(authorization.removeprefix("Bearer ").strip())
    if principal is None:
        raise AuthenticationRequired("the bearer token is invalid")
    return principal


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
        if isinstance(exc, AuthenticationRequired):
            status_code = 401
        elif isinstance(exc, TicketNotFound):
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
            headers={"X-Request-ID": request.state.request_id},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        error_code = "invalid_ticket_input"
        if any(
            error.get("type") == "json_invalid"
            or (error.get("type") == "missing" and error.get("loc") == ("body",))
            for error in exc.errors()
        ):
            error_code = "invalid_json"
        status_code = 400 if error_code == "invalid_json" else 422
        return JSONResponse(
            status_code=status_code,
            content={
                "code": error_code,
                "message": "request validation failed",
                "request_id": request.state.request_id,
                "data": {"errors": jsonable_encoder(exc.errors())},
            },
            headers={"X-Request-ID": request.state.request_id},
        )

    @app.exception_handler(Exception)
    async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "unhandled request error",
            extra={"request_id": request.state.request_id},
        )
        return JSONResponse(
            status_code=500,
            content={
                "code": "internal_error",
                "message": "internal error",
                "request_id": request.state.request_id,
                "data": None,
            },
            headers={"X-Request-ID": request.state.request_id},
        )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/v1/tickets", status_code=201, response_model=ApiResponse[Ticket])
    async def create_ticket(
        command: TicketCreate,
        request: Request,
        principal: Principal = Depends(get_principal),
        ticket_service: TicketService = Depends(get_service),
    ) -> ApiResponse[Ticket]:
        ticket = await ticket_service.create(principal.tenant_id, command)
        logger.info("ticket_created", extra={"ticket_id": str(ticket.id)})
        return ApiResponse(
            code="ok",
            message="created",
            request_id=request.state.request_id,
            data=ticket,
        )

    @app.get("/api/v1/tickets/{ticket_id}", response_model=ApiResponse[Ticket])
    async def get_ticket(
        ticket_id: TicketID,
        request: Request,
        principal: Principal = Depends(get_principal),
        ticket_service: TicketService = Depends(get_service),
    ) -> ApiResponse[Ticket]:
        ticket = await ticket_service.get(ticket_id, principal.tenant_id)
        return _success(request, ticket)

    @app.get("/api/v1/tickets", response_model=ApiResponse[list[Ticket]])
    async def list_tickets(
        request: Request,
        principal: Principal = Depends(get_principal),
        limit: int = Query(default=20, ge=1, le=100),
        ticket_service: TicketService = Depends(get_service),
    ) -> ApiResponse[list[Ticket]]:
        tickets = await ticket_service.list_for_tenant(principal.tenant_id)
        return ApiResponse(
            code="ok",
            message="ok",
            request_id=request.state.request_id,
            data=list(tickets[:limit]),
        )

    @app.post("/api/v1/tickets/{ticket_id}/close", response_model=ApiResponse[Ticket])
    async def close_ticket(
        ticket_id: TicketID,
        command: TicketClose,
        request: Request,
        principal: Principal = Depends(get_principal),
        ticket_service: TicketService = Depends(get_service),
    ) -> ApiResponse[Ticket]:
        ticket = await ticket_service.close(
            ticket_id=ticket_id,
            tenant_id=principal.tenant_id,
            expected_version=command.expected_version,
        )
        return _success(request, ticket)

    return app


def _success(request: Request, ticket: Ticket) -> ApiResponse[Ticket]:
    return ApiResponse(
        code="ok",
        message="ok",
        request_id=request.state.request_id,
        data=ticket,
    )


app = create_app()
