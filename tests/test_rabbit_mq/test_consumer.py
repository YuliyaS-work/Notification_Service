import logging

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from rabbit_mq.consumer import handle_message, iterate_queue, consume_general, \
    consume_message, consume_dlq
from core.config import settings


@pytest.mark.asyncio
@patch("rabbit_mq.consumer.process_message", new_callable=AsyncMock)
async def test_handle_message_main_success(mock_process):
    # Arrange
    message = MagicMock()
    message.body = b"test"
    repository = MagicMock()

    # Act
    await handle_message(message, repository, settings.queue_name_message)

    # Assert
    mock_process.assert_awaited_once_with("test", message, repository)


@pytest.mark.asyncio
@patch("rabbit_mq.consumer.process_message", new_callable=AsyncMock)
async def test_handle_message_main_error(mock_process, caplog):
    # Arrange
    message = MagicMock()
    message.body = b"test_body"
    repository = MagicMock()
    mock_process.side_effect=Exception()

    # Act
    with caplog.at_level(logging.ERROR):
        await handle_message(message, repository, settings.queue_name_message)

    # Assert
    assert "Error: failed message processing in" in caplog.text


@pytest.mark.asyncio
@patch("rabbit_mq.consumer.process_dlq_message", new_callable=AsyncMock)
async def test_handle_message_dlq_success(mock_dlq):
    # Arrange
    message = MagicMock()
    message.body = b"fake_body"

    # Act
    await handle_message(message, None, settings.queue_name_dlq)

    # Assert
    mock_dlq.assert_awaited_once_with(message)


@pytest.mark.asyncio
@patch("rabbit_mq.consumer.handle_message", new_callable=AsyncMock)
async def test_iterate_queue_calls_handle_message(mock_handler):
    # Arrange
    msg1 = MagicMock(body=b"fake_body1")
    msg2 = MagicMock(body=b"fake_body2")

    async def fake_iter():
        yield msg1
        yield msg2

    queue = MagicMock()
    queue.iterator.return_value.__aenter__.return_value = fake_iter()

    # Act
    await iterate_queue(queue, MagicMock(), "queue")

    # Assert
    assert mock_handler.await_count == 2


@pytest.mark.asyncio
@patch("asyncio.sleep", new_callable=AsyncMock)
async def test_consume_generic_connection_closed(mock_sleep):
    # Arrange
    repository = MagicMock()
    connection = MagicMock()
    connection.is_closed = True

    mock_sleep.side_effect = [None, asyncio.CancelledError()]

    # Act
    with pytest.raises(asyncio.CancelledError):
        await consume_general(repository, connection, "queue_name", prefetch=None)

    # Assert
    mock_sleep.assert_called_with(5)
    connection.channel.assert_not_called()


@pytest.mark.asyncio
@patch("rabbit_mq.consumer.iterate_queue", new_callable=AsyncMock)
async def test_consume_generic_one_iteration(mock_iter):
    # Arrange
    connection = MagicMock()
    connection.is_closed = False

    def flip_closed():
        connection.is_closed = True
        return False

    async def empty_async_iter():
        if False:
            yield None

    queue = MagicMock()
    queue.iterator.return_value.__aenter__.return_value = empty_async_iter()

    channel = MagicMock()
    channel.__aenter__.return_value = channel
    channel.__aexit__.return_value = False
    channel.set_qos = AsyncMock()
    channel.get_queue = AsyncMock(return_value=queue)

    connection.channel = AsyncMock(side_effect=lambda: flip_closed() or channel)

    # Act
    task = asyncio.create_task(
        consume_general(connection, MagicMock(), "queue", prefetch=10)
    )
    await asyncio.sleep(0.01)
    task.cancel()

    # Assert
    mock_iter.assert_awaited_once()


@pytest.mark.asyncio
@patch("rabbit_mq.consumer.consume_general", new_callable=AsyncMock)
async def test_consume_message_wrapper(mock_general):
    # Arrange / Act
    await consume_message("repo", "conn")

    # Assert
    mock_general.assert_awaited_once_with(
        connection="conn",
        repository="repo",
        queue_name=settings.queue_name_message,
        prefetch=20,
    )


@pytest.mark.asyncio
@patch("rabbit_mq.consumer.consume_general", new_callable=AsyncMock)
async def test_consume_dlq_wrapper(mock_general):
    # Arrange / Act
    await consume_dlq("conn")

    # Assert
    mock_general.assert_awaited_once_with(
        connection="conn",
        repository=None,
        queue_name=settings.queue_name_dlq,
        prefetch=None,
    )