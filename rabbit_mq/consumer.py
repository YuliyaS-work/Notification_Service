"""
This file contains asynchronous RabbitMQ consumers.

They read messages from main, create channel,
iterate over incoming messages and pass them to the proper handlers.
"""
import asyncio
import logging
from typing import Any

from aio_pika.abc import AbstractQueue, AbstractRobustConnection
from motor.motor_asyncio import AsyncIOMotorClient

from core.config import settings
from services.message import process_message

logger = logging.getLogger(__name__)


async def handle_message(
        message,
        repository: object | None,
        queue_name: str,
        mongo: AsyncIOMotorClient[Any],
        connection: AbstractRobustConnection
) -> None:
    """Processes a single message from a main queue or DLQ."""
    try:
        await process_message(message, repository, mongo, connection)

        logger.info(f"Success: processing message from {queue_name} ")

    except Exception as e:
        logger.error(f"Error: failed message processing in {queue_name}: {e}")


async def iterate_queue(
        queue: AbstractQueue,
        repository: object | None,
        queue_name: str,
        mongo: AsyncIOMotorClient[Any],
        connection: AbstractRobustConnection
) -> None:
    """Iterates over messages in the main queue or DLQ."""
    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            await handle_message(message, repository, queue_name, mongo, connection)
    logger.info(f"Success: iterating over messages in {queue_name}")


async def consume_message(
        connection: AbstractRobustConnection,
        mongo: AsyncIOMotorClient[Any],
        repository: object | None,
        queue_name=settings.queue_name_message,
        prefetch=20,
) -> None:
    """
    Runs a persistent consumer loop for a RabbitMQ queue.

    Args:
        connection: Active RabbitMQ connection used to create channels.
        mongo: MongoDB client.
        repository: Repository instance for message processing.
        queue_name: Name of the queue.
        prefetch: Number of messages to prefetch (optional).
    Returns:
        None: The function runs indefinitely and does not return a value.
    """
    logger.info(f"Start: handling {queue_name}")

    while True:
        try:
            if connection.is_closed:
                await asyncio.sleep(5)
                continue

            channel = await connection.channel()
            logger.info(f"Created a channel for {queue_name}")

            try:
                async with channel:
                    if prefetch:
                        await channel.set_qos(prefetch_count=prefetch)

                    queue = await channel.get_queue(queue_name)
                    logger.info(f"Got queue={queue_name}")

                    await iterate_queue(queue, repository, queue_name, mongo, connection)
            finally:
                await channel.close()

            logger.info(f"Success: handled {queue_name}")

        except Exception as e:
            logger.error(f"Error: failed network connection for {queue_name}: {e}")
            await asyncio.sleep(5)
            continue