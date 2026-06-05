"""
This file contains asynchronous RabbitMQ consumers.

They read messages from main and DLQ queues, create channels,
iterate over incoming messages and pass them to the proper handlers.
"""
import asyncio
import logging

from aio_pika.abc import AbstractQueue, AbstractRobustConnection
from core.config import settings
from services.message import process_message, process_dlq_message

logger = logging.getLogger(__name__)


async def handle_message(
        message,
        repository: object | None,
        queue_name: str
) -> None:
    """Processes a single message from a main queue or DLQ."""
    body = message.body.decode()

    try:
        if queue_name == settings.queue_name_message:
            await process_message(body, message, repository)
        else:
            await process_dlq_message(message)

        logger.info(f"Success: processing message from {queue_name} ")

    except Exception as e:
        logger.error(f"Error: failed message processing in {queue_name}: {e}")


async def iterate_queue(
        queue: AbstractQueue,
        repository: object | None,
        queue_name: str
):
    """Iterates over messages in the main queue or DLQ."""
    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            await handle_message(message, repository, queue_name)
    logger.info(f"Success: iterating over messages in {queue_name}")


async def consume_general(
        connection: AbstractRobustConnection,
        repository: object | None,
        queue_name: str,
        prefetch=None
) -> None:
    """
    Runs a persistent consumer loop for a RabbitMQ queue.

    Args:
        connection: Active RabbitMQ connection used to create channels.
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

            async with channel:
                if prefetch:
                    await channel.set_qos(prefetch_count=prefetch)

                queue = await channel.get_queue(queue_name)
                logger.info(f"Got queue={queue_name}")

                await iterate_queue(queue, repository, queue_name)

            logger.info(f"Success: handled {queue_name}")

        except Exception as e:
            logger.error(f"Error: failed network connection for {queue_name}: {e}")
            await asyncio.sleep(5)
            continue


async def consume_message(
        repository: object | None,
        connection: AbstractRobustConnection
) -> None:
    """Starts consumer for the main queue."""
    logger.info("Start: launching consumer for main queue")

    await consume_general(
        connection=connection,
        repository=repository,
        queue_name=settings.queue_name_message,
        prefetch=20,
    )

    logger.info("Consumer for main queue stoped")


async def consume_dlq(connection: AbstractRobustConnection) -> None:
    """Starts consumer for DLQ."""
    logger.info("Start: launching consumer for DLQ")

    await consume_general(
        connection=connection,
        repository=None,
        queue_name=settings.queue_name_dlq,
        prefetch=None,
    )

    logger.info("Consumer for DLQ stoped")