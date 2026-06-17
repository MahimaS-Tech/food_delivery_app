from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class APIMessage(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    detail: str


class Money(BaseModel):
    cents: int = Field(ge=0)
    currency: str = "INR"

    @property
    def rupees(self) -> float:
        return self.cents / 100


class Timestamped(BaseModel):
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
