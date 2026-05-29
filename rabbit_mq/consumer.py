"""
This file contains consumers that read messages from RabbitMQ queues.
They listen for messages and send them to the proper handlers.
"""
import logging

from core.config import settings
from services.message import process_message, process_dlq_message

logger = logging.getLogger(__name__)


async def consume_message(repository, connection) -> None:
    """
    Consumes messages from the main queue and sends them to the handler.

    Args:
        repository: Repository used by the handler to interact with the database.
        connection: Active RabbitMQ connection used to create channels and consume messages.
    """
    logger.info("Start: handling main queue")

    async with connection:
        # Creating channel
        channel = await connection.channel()
        logger.info("Created a channel for main queue")

        # Taking no more than 20 messages in advance
        await channel.set_qos(prefetch_count=20)

        # Getting queue
        queue = await channel.get_queue(settings.queue_name_message)
        logger.info(f"Got queue={settings.queue_name_message}")

        # Processing messages in queue
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                body = message.body.decode()
                try:
                    await process_message(body, message, repository)
                    logger.info("Success: processing message from main queue")
                except Exception as e:
                    logger.error(f"Error: failed message processing: {e}")
                    continue


async def consume_dlq(connection) -> None:
    """
    Consumes messages from the dead‑letter queue and processes them.

    Args:
        connection: Active RabbitMQ connection used to create channels and consume messages.
    """
    logger.info("Start: handling dlq queue")

    async with connection:
        # Creating channel
        channel = await connection.channel()
        logger.info("Created a channel for dlq queue")

        # Getting queue
        queue = await channel.get_queue(settings.queue_name_dlq)
        logger.info(f"Got queue={settings.queue_name_dlq}")

        # Processing messages in queue
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                try:
                    await process_dlq_message(message)
                    logger.info("Success: processing message from dlq queue")
                except Exception as e:
                    logger.error(f"Error: failed dlq message processing: {e}")
                    continue
