"""
Provides unit tests for the MongoDB connection manager
covering connect, disconnect and collection access.
"""
import logging
from unittest.mock import patch, MagicMock, AsyncMock

import pytest


@pytest.mark.asyncio
@patch("db.config.AsyncIOMotorClient")
async def test_connect_db_success(mock_motor_client, mock_mongo_db, caplog):
    """Tests successful MongoDB connection initialization."""
    # Arrange
    db = mock_mongo_db
    mock_client = AsyncMock()
    mock_client.admin.command = AsyncMock(return_value={"ok": 1})
    mock_motor_client.return_value = mock_client

    # Act
    with caplog.at_level(logging.INFO):
        await db.connect_db()

    # Assert
    assert db.client is not None
    assert f"Connection to MongoDB established" in caplog.text
    mock_motor_client.assert_called_once_with("test_url", uuidrepresentation="standard")

@pytest.mark.asyncio
@patch("db.config.AsyncIOMotorClient")
async def test_connect_db_fail(mock_client, mock_mongo_db, caplog):
    """Tests MongoDB connection with failure."""
    # Arrange
    db = mock_mongo_db
    mock_client.side_effect = Exception("fake_error")

    # Act
    with caplog.at_level(logging.ERROR):
        await db.connect_db()

    # Assert
    assert f"Connection to MongoDB failed: fake_error" in caplog.text


def test_disconnect_db_success( mock_mongo_db, caplog):
    """Tests successful MongoDB disconnection."""
    # Arrange
    db = mock_mongo_db
    db.client = MagicMock()

    # Act
    with caplog.at_level(logging.INFO):
        db.disconnect_db()

    # Assert
    assert "Connection to MongoDB was closed" in caplog.text
    db.client.close.assert_called_once()


def test_messages_connected(mock_mongo_db):
    """Tests that the messages returns the expected collection."""
    # Arrange/Act
    db = mock_mongo_db
    db.client = {"notification": {"messages": "fake_collection"}}

    # Assert
    assert db.messages == "fake_collection"


def test_messages_not_connected(mock_mongo_db):
    """Tests that an error raises when the client is not connected."""
    # Arrange
    db = mock_mongo_db
    db.client = None

    # Act
    with pytest.raises(RuntimeError) as e:
        db.messages()

    # Assert
    assert str(e.value) == "MongoDB client is not connected"