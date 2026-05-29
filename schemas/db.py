"""
This file defines the schema to store reset‑password message.
It helps validate saved data and keeps the structure consistent in the database.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class StoredResetPasswordMessage(BaseModel):
    """
    Schema to store reset-password messages.
    """
    model_config = ConfigDict(populate_by_name = True)

    id: UUID = Field(alias = "_id")
    email: str
    subject: str
    body: str
    token: str
    published_at: datetime
    sent_at: datetime | None = None
    attempts: int = 0
    status: str | None = None