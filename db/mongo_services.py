"""
This file contains a repository class for working with reset‑password messages in MongoDB.
It provides simple methods to make indexes for searching, save, update, and read documents
from the messages collection.
"""
import logging
from datetime import datetime, timezone
from typing import Any

from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import IndexModel, ASCENDING

from schemas.db import StoredResetPasswordMessage

logger = logging.getLogger(__name__)


class MessageRepository:
    """Handles database operations for reset‑password messages."""

    def __init__(self, collection: AsyncIOMotorCollection) -> None:
        """Initializes the object with the given collection."""
        self.collection: AsyncIOMotorCollection = collection
        logging.info("Created MessageRepository instance")

    async def make_indexes(self) -> None:
        """Create indexes for searching."""
        try:
            indexes = [
                IndexModel([("email", ASCENDING)], name="idx_email"),
                IndexModel([("published_at", ASCENDING)], name="idx_published_at"),
                IndexModel(
                    [("sent_at", ASCENDING)],
                    name="idx_sent_at_ttl",
                    expireAfterSeconds=2592000,
                ),
            ]
            await self.collection.create_indexes(indexes)
            logger.info("MongoDB indexes created successfully")
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
            raise


    async def save_doc(self, data: StoredResetPasswordMessage, session=None) -> None:
        """Saves a new message document to the database."""
        doc = data.model_dump(by_alias=True)
        try:
            await self.collection.insert_one(doc, session=session)
            logger.info(f"Saved message with message_id={data.id}")
        except Exception as e:
            logger.error(f"Failed to save message with message_id={data.id}: {e}")
            raise


    async def get_doc(self, _id: str, session=None)-> dict[str, Any] | None:
        """Returns a message document by its token."""
        try:
            result =  await self.collection.find_one({"_id":_id}, session=session)
            if result:
                logger.info(f"Found message with message_id={_id}")
            else:
                logger.warning(f"Message not found with message_id={_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to find message with message_id={_id}: {e}")
            raise


    async def update_status_doc(self, _id: str, status: str, session=None) -> None:
        """Updates the message status and send time."""
        try:
            await self.collection.find_one_and_update({"_id": _id}, {"$set": {"status": status, "sent_at": datetime.now(timezone.utc)}}, session=session)
            logger.info(f"Updated message status with message_id={_id}")
        except Exception as e:
            logger.error(f"Failed to update message status with message_id={_id}: {e}")
            raise