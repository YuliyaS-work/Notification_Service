"""
This file contains a repository class for working with reset‑password messages in MongoDB.
It provides simple methods to save, update, and read documents from the messages collection.
"""
import logging
from typing import Any

from motor.motor_asyncio import AsyncIOMotorCollection

from schemas.db import StoredResetPasswordMessage

logger = logging.getLogger(__name__)


class MessageRepository:
    """Handles database operations for reset‑password messages."""

    def __init__(self, collection: AsyncIOMotorCollection) -> None:
        """Initializes the object with the given collection."""
        self.collection: AsyncIOMotorCollection = collection
        logging.info("Created MessageRepository instance")


    async def save_doc(self, data: StoredResetPasswordMessage) -> None:
        """Saves a new message document to the database."""
        doc = data.model_dump(by_alias=True)
        try:
            await self.collection.insert_one(doc)
            logger.info(f"Saved message with token={data.token}")
        except Exception as e:
            logger.error(f"Failed to save message with token={data.token}: {e}")
            raise

    async def delete_doc(self, token: str) -> None:
        """Deletes a message document by its token from database."""
        try:
            await self.collection.delete_one({"token": token})
            logger.info(f"Deleted message with token={token}")
        except Exception as e:
            logger.error(f"Failed to delete message with token={token}: {e}")
            raise


    async def increase_attempts(self, token: str) -> None:
        """Updates the number of sending attempts for a message."""
        try:
            await self.collection.update_one({"token": token}, {"$inc": {"attempts": 1}})
            logger.info(f"Updated message attempts  with token={token}")
        except Exception as e:
            logger.error(f"Failed to increase message attempts with token={token}: {e}")
            raise

    async def get_doc(self, token: str) -> dict[str, Any] | None:
        """Returns a message document by its token."""
        try:
            result =  await self.collection.find_one({"token": token})
            logger.info(f"Found message with token={token}")
            return result
        except Exception as e:
            logger.error(f"Failed to find message with token={token}: {e}")
            raise


    async def update_status_doc(self, token: str, status: str) -> None:
        """Updates the message status."""
        try:
            await self.collection.find_one_and_update({"token": token}, {"$set": {"status": status}})
            logger.info(f"Updated message status with token={token}")
        except Exception as e:
            logger.error(f"Failed to update message status with token={token}: {e}")
            raise