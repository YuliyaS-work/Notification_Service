"""
This file contains functions that process reset‑password messages from RabbitMQ.
They validate incoming data, update the database, and send emails when needed.
"""
import logging
from datetime import datetime
from typing import Any

import aio_pika
from aio_pika.abc import AbstractIncomingMessage, AbstractRobustConnection
from motor.motor_asyncio import AsyncIOMotorClient

from core.config import settings
from schemas.consumer import IncomingBodyMessage
from schemas.db import StoredResetPasswordMessage
from ses.ses_service import send_email

logger = logging.getLogger(__name__)


async def process_message(
        message: AbstractIncomingMessage,
        repository: Any,
        mongo:  AsyncIOMotorClient,
        connection: AbstractRobustConnection
) -> None:
    """
    Handles a reset‑password message and updates its status in the database if sending fails.

    Args:
        mongo: MongoDB client.
        connection: RabbitMQ connection.
        message: RabbitMQ message object providing ack/nack operations.
        repository: Repository for interacting with the message storage (MongoDB).
    Returns:
        None: The function removes the message from the queue or puts it back for another attempt.
    """
    logger.info("Start: handling message from main queue")

    # Validate incoming data otherwise deletes message fron queue
    try:
        validate_body = IncomingBodyMessage.model_validate_json(message.body)
        message_id = message.message_id

        if message_id is None:
            logger.error("Message has no message_id")
            await message.nack(requeue=False)
            return

        logger.info(f"Validated incoming message data, message ID={message_id}")

    except Exception as e:
        logger.error(f"Invalid body message: {e}")
        await message.nack(requeue=False)
        return

    # Check the message in the database to avoid duplicates
    doc = await repository.get_doc(message_id)
    if doc and doc["status"] == "sent":
        logger.info("Message was sent successfully.")
        await message.ack()
        return

    session = await mongo.client.start_session()

    try:
        async with session.start_transaction():

            # Create new message document in the database
            stored_data = StoredResetPasswordMessage(
                _id=message_id,
                email=validate_body.email,
                subject=validate_body.subject,
                body=validate_body.body,
                token=validate_body.token,
                published_at=datetime.fromisoformat(validate_body.datetime),
                status="pending"
            )

            await repository.save_doc(stored_data, session)
            doc = await repository.get_doc(message_id, session)

            logger.info("Created new document for message in the database")

            # Sending an email.
            await send_email(
                settings.ses_email_from,
                doc["email"],
                doc["subject"],
                doc["body"],
                doc["body"]
            )

            # Update status and send time message.
            await repository.update_status_doc(message_id, "sent", session)

            # Delete a message from main queue.
            await message.ack()

            logger.info(f"Success: sending email, message_id={message_id}")

    except Exception as e:
        logger.error(f"Error: failed sending email, message_id={message_id}: {e}")

        # Increase the number of sending attempts.
        attempts = int(message.headers.get("x-retry-count", 0))
        attempts += 1

        # Return the message to main queue for next retry
        if attempts < 5:

            # Publish message with new retry count header.
            try:
                channel = await connection.channel()
                await channel.default_exchange.publish(
                    aio_pika.Message(
                        body=message.body,
                        message_id=message_id,
                        headers={"x-retry-count":attempts},
                        content_type="application/json"
                    ),
                    routing_key="reset-password-stream",
                )

                await message.ack()

                logger.info(f"Returned renew message document to main queue, message_id={message_id}, attempts={attempts}")

            except Exception as e:
                await message.nack(requeue=True)
                logger.warning(f"Failed retry to publish message, message_id={message_id}: {e}")

        # Return the message to DLQ
        elif attempts >= 5:
            await message.nack(requeue=False)
            logger.warning(f"Moved message to dlq, message_id={message_id}, attempts={attempts}")