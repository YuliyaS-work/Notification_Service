"""
This file defines the schema for an incoming reset‑password message.
It is used to validate the data received from the message queue.
"""
from pydantic import BaseModel


class IncomingResetPasswordMessage(BaseModel):
    """
    Schema for incoming reset-password messages.
    """
    subject: str
    body: str
    email: str
    token: str
    datetime: str