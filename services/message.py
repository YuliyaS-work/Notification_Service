"""
This file contains functions that process reset‑password messages from RabbitMQ.
They validate incoming data, update the database, and send emails when needed.
"""
import uuid
from datetime import datetime

from core.config import settings
from schemas.consumer import IncomingResetPasswordMessage
from schemas.db import StoredResetPasswordMessage
from ses.ses_service import send_email


async def process_message(raw_body: str, message, repository):
    """
    Handles a reset‑password message and updates its status in the database if sending fails.

    Args:
        raw_body: Raw JSON body received from RabbitMQ.
        message: RabbitMQ message object providing ack/nack operations.
        repository: Repository for interacting with the message storage (MongoDB).
    Returns:
        None: The function removes the message from the queue or puts it back for another attempt.
    """

    # Validates incoming data otherwise deletes message fron queue
    try:
        validate_data = IncomingResetPasswordMessage.model_validate_json(raw_body)
        token = validate_data.token
    except:
        await message.ack()
        return

    # Gets the message document from the database
    doc = await repository.get_doc(token)

    # Creates new message document if it doesn't exist in the database
    if not doc:
        stored_data = StoredResetPasswordMessage(
            _id=uuid.uuid4(),
            email=validate_data.email,
            subject=validate_data.subject,
            body=validate_data.body,
            token=validate_data.token,
            published_at=datetime.fromisoformat(validate_data.datetime),
        )

        try:
            await repository.save_doc(stored_data)
            doc = await repository.get_doc(token)
        except:
            # Returns to queue if storing to the database failed
            await message.nack(requeue=True)
            return

    # Sends email if success deleting from queue and the database otherwise return to RabbitMq
    try:
        await send_email(
            settings.ses_email_from,
            doc["email"],
            doc["subject"],
            doc["body"],
            doc["body"]
        )
        await message.ack()
        await repository.delete_doc(token)

    except:
        # Increases attempts the for message
        await repository.increase_attempts(token)

        # Gets updates message data
        doc = await repository.get_doc(token)

        # Returns the message to main queue for next retry
        if doc["attempts"] < 5:
            await repository.update_status_doc(token, "failed")
            await message.nack(requeue=True)

        # Returns the message to dead letter queue
        elif doc["attempts"] >=5:
            await repository.update_status_doc(token, "dlq")
            await message.nack(requeue=False)


async def process_dlq_message(message):
    """Handles messages that were moved to the dead letter queue."""

    # Delete from dead letter queue, the message is in the database.
    await message.ack()