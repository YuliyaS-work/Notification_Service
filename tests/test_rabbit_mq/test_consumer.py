"""Provides unit tests for message handling, queue iteration, and consumers of DLQ and main queue in RabbitMQ."""
import logging

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from rabbit_mq.consumer import handle_message, iterate_queue, consume_message
from core.config import settings


@pytest.mark.asyncio
@patch("rabbit_mq.consumer.process_message", new_callable=AsyncMock)
async def test_handle_message_main_success(
        mock_process,
        mock_mongo,
        mock_connection
):
    """Tests that handle_message() correctly processes a main queue message."""
    # Arrange
    message = MagicMock()
    message.body = b"test"
    repository = MagicMock()

    # Act
    await handle_message(message, repository, settings.queue_name_message, mock_mongo, mock_connection)

    # Assert
    mock_process.assert_awaited_once_with(message, repository, mock_mongo, mock_connection)


@pytest.mark.asyncio
@patch("rabbit_mq.consumer.process_message", new_callable=AsyncMock)
async def test_handle_message_main_error(
        mock_process,
        mock_mongo,
        mock_connection,
        caplog
):
    """Tests that handle_message() fails while processing a main-queue message."""
    # Arrange
    message = MagicMock()
    message.body = b"test_body"
    repository = MagicMock()
    mock_process.side_effect=Exception()

    # Act
    with caplog.at_level(logging.ERROR):
        await handle_message(message, repository, mock_mongo, mock_connection, settings.queue_name_message)

    # Assert
    assert "Error: failed message processing in" in caplog.text


@pytest.mark.asyncio
@patch("rabbit_mq.consumer.handle_message", new_callable=AsyncMock)
async def test_iterate_queue_success(
        mock_handler,
        mock_mongo,
        mock_connection
):
    """Tests that iterate_queue iterate each message in the iterator successfully."""
    # Arrange
    message1 = MagicMock(body=b"fake_body1")
    message2 = MagicMock(body=b"fake_body2")

    async def fake_iter():
        yield message1
        yield message2

    queue = MagicMock()
    queue.iterator.return_value.__aenter__.return_value = fake_iter()

    # Act
    await iterate_queue(queue, MagicMock(), "queue", mock_mongo, mock_connection)

    # Assert
    assert mock_handler.await_count == 2


@pytest.mark.asyncio
@patch("asyncio.sleep", new_callable=AsyncMock)
async def test_consume_message_connection_closed(
        mock_sleep,
        mock_mongo,
        mock_connection,
        mock_repo
):
    """Tests that consume_general waits when the connection is closed and does not create a channel."""
    # Arrange
    mock_connection.is_closed = True
    mock_connection.channel = AsyncMock()

    mock_sleep.side_effect = [None, asyncio.CancelledError()]

    # Act
    with pytest.raises(asyncio.CancelledError):
        await consume_message(mock_connection, mock_mongo, mock_repo,"queue_name", prefetch=None)

    # Assert
    mock_sleep.assert_called_with(5)


@pytest.mark.asyncio
@patch("rabbit_mq.consumer.iterate_queue", new_callable=AsyncMock)
async def test_consume_message_one_iteration(
        mock_iterate_queue,
        mock_mongo,
        mock_connection,
        mock_repo
):
    """Tests that consume_message performs a single iteration and calls iterate_queue() once."""
    # Arrange
    mock_connection.is_closed = False

    channel = AsyncMock()
    channel.set_qos = AsyncMock()
    channel.declare_queue = AsyncMock()
    channel.declare_exchange = AsyncMock()

    main_queue = AsyncMock()
    dlq = AsyncMock()
    dlq.bind = AsyncMock()

    channel.declare_queue.side_effect = [main_queue, dlq]
    mock_connection.channel = AsyncMock(return_value=channel)

    # one iteration
    async def first_and_stop(*args, **kwargs):
        mock_connection.is_closed = True
        await asyncio.sleep(0)

    mock_iterate_queue.side_effect = first_and_stop

    # Act
    task = asyncio.create_task(
        consume_message(mock_connection, mock_mongo, mock_repo,"queue_name", prefetch=None)
    )
    await asyncio.sleep(0.01)
    task.cancel()

    # Assert
    mock_iterate_queue.assert_awaited_once()