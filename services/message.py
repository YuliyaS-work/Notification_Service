"""
This file contains functions that process reset‑password messages from RabbitMQ.
They validate incoming data, update the database, and send emails when needed.
"""
import logging
import uuid
from datetime import datetime
from typing import Any

from aio_pika.abc import AbstractIncomingMessage

from core.config import settings
from schemas.consumer import IncomingResetPasswordMessage
from schemas.db import StoredResetPasswordMessage
from ses.ses_service import send_email

logger = logging.getLogger(__name__)


async def process_message(
        raw_body: str,
        message: AbstractIncomingMessage,
        repository: Any
) -> None:
    """
    Handles a reset‑password message and updates its status in the database if sending fails.

    Args:
        raw_body: Raw JSON body received from RabbitMQ.
        message: RabbitMQ message object providing ack/nack operations.
        repository: Repository for interacting with the message storage (MongoDB).
    Returns:
        None: The function removes the message from the queue or puts it back for another attempt.
    """
    logger.info("Start: handling message from main queue")

    # Validate incoming data otherwise deletes message fron queue
    try:
        validate_data = IncomingResetPasswordMessage.model_validate_json(raw_body)
        token = validate_data.token
        logger.info(f"Received message token={token}")
    except Exception as e:
        logger.error(f"Invalid body message: {e}")
        await message.ack()
        return

    # Get the message document from the database
    doc = await repository.get_doc(token)

    # Create new message document if it doesn't exist in the database
    if not doc:
        logger.info("Creating new message document in the database")
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
            logger.info("Created new document for message in the database")
        except Exception as e:
            # Return to queue if storing to the database failed
            logger.error(f"Failed to save message into the database: {e}")
            await message.nack(requeue=True)
            return

    # Send email if success deleting from queue and the database otherwise return to RabbitMq
    try:
        await send_email(
            settings.ses_email_from,
            doc["email"],
            doc["subject"],
            doc["body"],
            doc["body"]
        )
        logger.info(f"Success: sending email, token={token}")
        await message.ack()
        await repository.delete_doc(token)

    except Exception as e:
        logger.error(f"Error: failed sending email, token={token}: {e}")

        try:
            # Increase attempts the for message and get updates message data
            await repository.increase_attempts(token)
            doc = await repository.get_doc(token)

            if not doc:
                logger.error("Doc is not found in DB")
                await message.nack(requeue=False)
                return

            attempts = doc.get("attempts")
            logger.warning(f"Updated message attempts, token={token} attempts={attempts}")

            # Return the message to dead letter queue
            if attempts < 5:
                await repository.update_status_doc(token, "failed")
                await message.nack(requeue=True)
                logger.info(f"Returned message document to main queue token={token}")

            # Return the message to main queue for next retry
            elif attempts >= 5:
                await repository.update_status_doc(token, "dlq")
                await message.nack(requeue=False)
                logger.warning(f"Moved message to dlq, token={token}")


        except Exception as exc:
            logger.critical(f"Internal error in exception handler: {exc}")
            await message.nack(requeue=True)


async def process_dlq_message(message: AbstractIncomingMessage) -> None:
    """Handles messages that were moved to the dead letter queue."""
    await message.ack() # Delete from dead letter queue, the message is in the database.
    logger.warning("DLQ message was acknowledged")