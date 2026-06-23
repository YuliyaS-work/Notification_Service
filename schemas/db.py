"""
This file defines the schema to store reset‑password message.
It helps validate saved data and keeps the structure consistent in the database.
"""
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class StoredResetPasswordMessage(BaseModel):
    """
    Schema to store reset-password messages.
    """
    model_config = ConfigDict(populate_by_name = True)

    id: str = Field(alias="_id")
    email: str
    subject: str
    body: str
    token: str
    published_at: datetime
    sent_at: datetime | None = None
    status: str | None = None