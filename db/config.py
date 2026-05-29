"""
This file defines a small helper class for working with MongoDB using Motor.
It creates a client connection and gives easy access to the message collection.
"""
import logging

from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)


class MongoDB:
    """A class that manages a MongoDB connection."""

    def __init__(self, url):
        """Initializes the object with the given parameters."""
        self.url = url
        self.client: AsyncIOMotorClient | None = None
        logging.info("MongoDB instance was created")


    def connect_db(self):
        """Creates a MongoDB client using the given URL."""
        try:
            self.client = AsyncIOMotorClient(self.url, uuidrepresentation="standard")
        except Exception as e:
            logger.error(f"Connection to MongoDB failed: {e}")


    def disconnect_db(self):
        """Closes the MongoDB client if it is active."""
        if self.client:
            self.client.close()
            logger.info("Connection to MongoDB was closed")


    @property
    def messages(self):
        """Returns the message collection from the notification database."""
        if not self.client:
            logger.error("MongoDB client is not connected")
            raise RuntimeError("MongoDB client is not connected")
        return self.client["notification"]["messages"]