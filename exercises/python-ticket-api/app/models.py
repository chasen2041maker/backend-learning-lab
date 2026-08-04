from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Generic, TypeVar
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TicketStatus(StrEnum):
    OPEN = "open"
    CLOSED = "closed"


class StrictInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TicketCreate(StrictInput):
    title: str = Field(min_length=1, max_length=200)

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("title must not be blank")
        return stripped


class TicketClose(StrictInput):
    expected_version: int = Field(ge=1)


class Principal(BaseModel):
    model_config = ConfigDict(frozen=True)

    subject: str
    tenant_id: str


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
    def new(cls, command: TicketCreate, tenant_id: str) -> Ticket:
        now = datetime.now(UTC)
        return cls(
            id=uuid4(),
            tenant_id=tenant_id,
            title=command.title,
            status=TicketStatus.OPEN,
            version=1,
            created_at=now,
            updated_at=now,
        )


T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: str
    message: str
    request_id: str
    data: T | None
