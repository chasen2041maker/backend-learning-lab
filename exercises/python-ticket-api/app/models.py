from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TicketStatus(StrEnum):
    OPEN = "open"
    CLOSED = "closed"


class TicketCreate(BaseModel):
    tenant_id: str = Field(min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")
    title: str = Field(min_length=1, max_length=200)

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("title must not be blank")
        return stripped


class TicketClose(BaseModel):
    tenant_id: str = Field(min_length=1, max_length=64)
    expected_version: int = Field(ge=1)


class Ticket(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    tenant_id: str
    title: str
    status: TicketStatus
    version: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def new(cls, command: TicketCreate) -> Ticket:
        now = datetime.now(UTC)
        return cls(
            id=uuid4(),
            tenant_id=command.tenant_id,
            title=command.title,
            status=TicketStatus.OPEN,
            version=1,
            created_at=now,
            updated_at=now,
        )


class ApiResponse(BaseModel):
    code: str
    message: str
    request_id: str
    data: object | None
