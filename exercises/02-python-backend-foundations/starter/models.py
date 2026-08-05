from __future__ import annotations

from datetime import UTC, datetime
from typing import Generic, TypeVar
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class TicketCreate(StrictInput):
    title: str = Field(min_length=1, max_length=200)
    # TODO: add priority with a default and an explicit set of allowed values.

    @field_validator("title", mode="before")
    @classmethod
    def trim_title(cls, value: object) -> str:
        if not isinstance(value, str):
            raise ValueError("title must be a string")
        return value.strip()


class Ticket(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    tenant_id: str
    title: str
    # TODO: expose priority on internal state and output.
    created_at: datetime

    @classmethod
    def new(cls, command: TicketCreate, tenant_id: str) -> Ticket:
        return cls(
            id=uuid4(),
            tenant_id=tenant_id,
            title=command.title,
            created_at=datetime.now(UTC),
        )


T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: str
    message: str
    request_id: str
    data: T | None
