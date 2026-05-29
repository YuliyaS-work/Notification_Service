"""
This file defines a small helper class for working with MongoDB using Motor.
It creates a client connection and gives easy access to the message collection.
"""
from motor.motor_asyncio import AsyncIOMotorClient


class MongoDB:
    """A class that manages a MongoDB connection."""

    def __init__(self, url):
        """Initializes the object with the given parameters."""
        self.url = url
        self.client: AsyncIOMotorClient | None = None


    def connect_db(self):
        """Creates a MongoDB client using the given URL."""
        self.client = AsyncIOMotorClient(self.url, uuidrepresentation="standard")


    def disconnect_db(self):
        """Closes the MongoDB client if it is active."""
        if self.client:
            self.client.close()


    @property
    def messages(self):
        """Returns the message collection from the notification database."""
        return self.client["notification"]["messages"]