"""
This file contains a repository class for working with reset‑password messages in MongoDB.
It provides simple methods to save, update, and read documents from the messages collection.
"""
from schemas.db import StoredResetPasswordMessage


class MessageRepository:
    """Handles database operations for reset‑password messages."""

    def __init__(self, collection):
        """Initializes the object with the given collection."""
        self.collection = collection


    async def save_doc(self, data: StoredResetPasswordMessage):
        """Saves a new message document to the database."""
        doc = data.model_dump(by_alias=True)
        await self.collection.insert_one(doc)


    async def delete_doc(self, token: str):
        """Deletes a message document by its token from database."""
        await self.collection.delete_one({"token": token})


    async def increase_attempts(self, token: str):
        """Updates the number of sending attempts for a message."""
        await self.collection.update_one({"token": token}, {"$inc": {"attempts": 1}})


    async def get_doc(self, token: str):
        """Returns a message document by its token."""
        result =  await self.collection.find_one({"token": token})
        return result


    async def update_status_doc(self, token: str, status: str):
        """Updates the message status."""
        await self.collection.update_one({"token": token}, {"$set": {"status": status}})