"""
This file defines the Settings class that loads app configuration from environment variables.
It helps the service use the correct settings for RabbitMQ, MongoDB, and AWS SES.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global configuration settings."""
    rabbitmq_url: str
    queue_name_message: str
    queue_name_dlq: str

    mongo_url: str

    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str
    ses_email_from: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()