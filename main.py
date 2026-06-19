"""
This module initializes the service infrastructure, connects to MongoDB and RabbitMQ,
and starts consumer that process incoming messages.
It also handles graceful shutdown on system signals.
"""
import asyncio
import logging
import signal

import aio_pika

from core.config import settings
from core.logging import setup_logging
from db.config import MongoDB
from db.mongo_services import MessageRepository
from rabbit_mq.consumer import  consume_message

logger = logging.getLogger(__name__)


async def main() -> None:
    """
    Sets up database and RabbitMQ connections, registers shutdown handlers,
    and starts consumer.
    """
    # Starts logging
    listener = setup_logging()
    logger.info("Initialized logging")

    # A database client
    mongo = MongoDB(settings.mongo_url)
    await mongo.connect_db()
    logger.info("Created connection to the database")

    # A RabbitMQ connection
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    logger.info("Created connection to RabbitMQ")

    # Closes RabbitMq and MongoDB connections  during graceful shutdown
    async def shutdown():
        if connection:
            await connection.close()
            logger.info("Stopped connection to RabbitMQ")
        if mongo:
            mongo.disconnect_db()
            logger.info("Stopped connection to the database")
        logger.info("Stopped logging listener")
        listener.stop()


    # Creates a repository to work with MongoDB
    repository = MessageRepository(mongo.messages)
    logger.info("Initialized MessageRepository")
    await repository.make_indexes()
    logger.info("MongoDB indexes created")

    # Runs shutdown when the service stops
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGTERM, lambda:asyncio.create_task(shutdown()))
    loop.add_signal_handler(signal.SIGINT, lambda:asyncio.create_task(shutdown()))

    # Starts consumer
    logger.info("Starting message consumers")

    if mongo.client is None:
        raise RuntimeError("MongoDB client is not initialized")

    await consume_message(connection, mongo, repository)


if __name__ == "__main__":
    asyncio.run(main())