from __future__ import annotations

import re
from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated, Generic, TypeVar
from uuid import UUID, uuid4

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, field_validator

UUID_V4_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def validate_uuid_v4_text(value: object) -> str:
    if not isinstance(value, str) or UUID_V4_PATTERN.fullmatch(value) is None:
        raise ValueError("ticket id must be a canonical UUID v4 string")
    return value


TicketID = Annotated[UUID, BeforeValidator(validate_uuid_v4_text)]


class TicketStatus(StrEnum):
    OPEN = "open"
    CLOSED = "closed"


class StrictInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class TicketCreate(StrictInput):
    title: str = Field(min_length=1, max_length=200)

    @field_validator("title", mode="before")
    @classmethod
    def trim_title_before_length_validation(cls, value: object) -> str:
        if not isinstance(value, str):
            raise ValueError("title must be a string")
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
