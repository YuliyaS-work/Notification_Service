"""
This file contains consumers that read messages from RabbitMQ queues.
They listen for messages and send them to the proper handlers.
"""
from core.config import settings
from services.message import process_message, process_dlq_message


async def consume_message(repository, connection) -> None:
    """
    Consumes messages from the main queue and sends them to the handler.

    Args:
        repository: Repository used by the handler to interact with the database.
        connection: Active RabbitMQ connection used to create channels and consume messages.
    """

    async with connection:
        # Creating channel
        channel = await connection.channel()

        # Taking no more than 20 messages in advance
        await channel.set_qos(prefetch_count=20)

        # Getting queue
        queue = await channel.get_queue(settings.queue_name_message)

        # Processing messages in queue
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                body = message.body.decode()
                await process_message(body, message, repository)


async def consume_dlq(connection) -> None:
    """
    Consumes messages from the dead‑letter queue and processes them.

    Args:
        connection: Active RabbitMQ connection used to create channels and consume messages.
    """
    async with connection:
        # Creating channel
        channel = await connection.channel()

        # Getting queue
        queue = await channel.get_queue(settings.queue_name_dlq)

        # Processing messages in queue
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                await process_dlq_message(message, )