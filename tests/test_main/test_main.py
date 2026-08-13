"""Provides unit test for the application startup process."""
from unittest.mock import patch, AsyncMock, Mock

import pytest

from main import main


@pytest.mark.asyncio
@patch("main.asyncio.get_running_loop")
@patch("main.consume_message")
@patch("main.MessageRepository")
@patch("main.MongoDB")
@patch("main.aio_pika.connect_robust")
@patch("main.setup_logging")
async def test_main_success(
        mock_setup_logging,
        mock_connect,
        mock_mongo,
        mock_repo,
        mock_consume,
        mock_get_running_loop
):
    """Tests that the application starts successfully."""
    # Arrange
    listener = Mock()
    mock_setup_logging.return_value = listener

    mongo = AsyncMock()
    mongo.client = object()
    mongo.messages = object()
    mock_mongo.return_value = mongo

    connection = AsyncMock()
    mock_connect.return_value = connection

    repository = AsyncMock()
    mock_repo.return_value = repository

    loop = Mock()
    mock_get_running_loop.return_value = loop

    # Act
    await main()

    # Assert
    mongo.connect_db.assert_called_once()
    repository.make_indexes.assert_called_once()
    assert loop.add_signal_handler.call_count == 2
    mock_consume.assert_called_once_with(connection, mongo, repository)