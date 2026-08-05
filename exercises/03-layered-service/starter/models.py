from pydantic import BaseModel, ConfigDict, Field


class CloseTicket(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    expected_version: int = Field(ge=1)
