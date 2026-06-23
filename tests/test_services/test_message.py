"""Provides unit tests for message processing logic  and error handling."""
import logging
from unittest.mock import patch, AsyncMock, Mock

import pytest

from services.message import process_message


@pytest.mark.asyncio
@patch("services.message.send_email")
async def test_process_message_message_in_db(
        mock_send_email,
        mock_incoming_data,
        mock_repo,
        mock_mongo,
        mock_connection,
        caplog
):
    """Tests that a message already stored in the database."""
    # Arrange
    message = AsyncMock()
    message.body = mock_incoming_data.encode()
    message.message_id = "fake_id"
    message.ack = AsyncMock()
    mock_repo.get_doc = AsyncMock(return_value={
        "email": "user@example.com",
        "subject": "reset password",
        "body": "click the link",
        "token": "fake_token",
        "status": "sent"
    })

    # Act
    with caplog.at_level(logging.INFO):
        await process_message(message, mock_repo, mock_mongo, mock_connection)

    # Assert
    assert "Message was sent successfully." in caplog.text
    message.ack.assert_called_once()


@pytest.mark.asyncio
@patch("services.message.IncomingBodyMessage.model_validate_json")
@patch("services.message.send_email")
async def test_process_message_invalid_body(
        mock_send_email,
        mock_validate_incoming_data,
        mock_repo,
        mock_mongo,
        mock_connection,
        caplog
):
    """Tests that incoming message body is invalid."""
    # Arrange
    mock_validate_incoming_data.side_effect = Exception()
    message = AsyncMock()
    message.ack = AsyncMock()

    # Act
    with caplog.at_level(logging.ERROR):
        await process_message(message, mock_repo, mock_mongo, mock_connection)

    # Assert
    assert "Invalid body message" in caplog.text
    mock_send_email.assert_not_called()
    message.nack.assert_called_once_with(requeue=False)


@pytest.mark.asyncio
@patch("services.message.send_email")
async def test_process_message_not_send_attempts_lt_5(
        mock_send_email,
        mock_incoming_data,
        mock_repo,
        mock_connection,
        mock_mongo,
        mock_data,
        caplog
):
    """Tests email sending failure when attempts less than five."""
    # Arrange
    message = AsyncMock()
    message.body = mock_incoming_data.encode()
    message.message_id = "fake_id"
    message.headers = {"x-retry-count": 2}
    message.ack = AsyncMock()

    mock_repo.get_doc = AsyncMock(side_effect=[
        None,
        {
            "email": "user@example.com",
            "subject": "reset password",
            "body": "click the link",
            "token": "fake_token",
            "status": "sent"
        }
    ])
    mock_repo.save_doc = AsyncMock()
    mock_repo.update_status_doc = AsyncMock()
    mock_send_email.side_effect = Exception()

    mock_session = AsyncMock()
    mock_transaction = AsyncMock()

    mock_transaction.__aenter__.return_value = None
    mock_transaction.__aexit__.return_value = None

    mock_session.start_transaction = Mock(return_value=mock_transaction)
    mock_mongo.client.start_session.return_value = mock_session

    channel = AsyncMock()
    mock_connection.channel = AsyncMock(return_value=channel)

    # Act
    with caplog.at_level(logging.ERROR):
        await process_message(message, mock_repo, mock_mongo, mock_connection)

    # Assert
    assert "Error: failed sending email, message_id=fake_id" in caplog.text
    mock_send_email.assert_called_once()
    mock_connection.channel.assert_called_once()
    channel.default_exchange.publish.assert_called_once()
    message.ack.assert_called_once()


@pytest.mark.asyncio
@patch("services.message.send_email")
async def test_process_message_not_send_attempts_ge_5(
        mock_send_email,
        mock_incoming_data,
        mock_repo,
        mock_connection,
        mock_mongo,
        caplog
):
    """Tests email sending failure when attempts greater than or equal to five."""
    # Arrange
    message = AsyncMock()
    message.body = mock_incoming_data.encode()
    message.message_id = "fake_id"
    message.headers = {"x-retry-count": 5}
    message.nack = AsyncMock()

    mock_repo.get_doc = AsyncMock(side_effect=[
        None,
        {
            "email": "user@example.com",
            "subject": "reset password",
            "body": "click the link",
            "token": "fake_token",
            "status": "sent"
        }
    ])
    mock_repo.save_doc = AsyncMock()
    mock_repo.update_status_doc = AsyncMock()
    mock_send_email.side_effect = Exception()

    mock_session = AsyncMock()
    mock_transaction = AsyncMock()

    mock_transaction.__aenter__.return_value = None
    mock_transaction.__aexit__.return_value = None

    mock_session.start_transaction = Mock(return_value=mock_transaction)
    mock_mongo.client.start_session.return_value = mock_session

    # Act
    with caplog.at_level(logging.ERROR):
        await process_message(message, mock_repo, mock_mongo, mock_connection)

    # Assert
    assert "Error: failed sending email" in caplog.text
    mock_send_email.assert_called_once()
    message.nack.assert_called_once_with(requeue=False)


@pytest.mark.asyncio
@patch("services.message.send_email")
async def test_process_message_not_message_id(
        mock_send_email,
        mock_incoming_data,
        mock_repo,
        mock_mongo,
        mock_connection,
        caplog
):
    """Tests that a message does not have ID."""
    # Arrange
    message = AsyncMock()
    message.body = mock_incoming_data.encode()
    message.message_id = None
    message.nack = AsyncMock()

    # Act
    with caplog.at_level(logging.ERROR):
        await process_message(message, mock_repo, mock_mongo, mock_connection)

    # Assert
    assert "Message has no message_id" in caplog.text
    message.nack.assert_called_once_with(requeue=False)


@pytest.mark.asyncio
@patch("services.message.send_email")
async def test_process_message_success(
        mock_send_email,
        mock_incoming_data,
        mock_repo,
        mock_connection,
        mock_mongo,
        caplog
):
    """Tests email sending failure when attempts greater than or equal to five."""
    # Arrange
    message = AsyncMock()
    message.body = mock_incoming_data.encode()
    message.message_id = "fake_id"
    message.headers = {"x-retry-count": 0}
    message.ack = AsyncMock()

    mock_repo.get_doc = AsyncMock(side_effect=[
        None,
        {
            "email": "user@example.com",
            "subject": "reset password",
            "body": "click the link",
            "token": "fake_token",
            "status": "sent"
        }
    ])
    mock_repo.save_doc = AsyncMock()
    mock_repo.update_status_doc = AsyncMock()

    mock_session = AsyncMock()
    mock_transaction = AsyncMock()

    mock_transaction.__aenter__.return_value = None
    mock_transaction.__aexit__.return_value = None

    mock_session.start_transaction = Mock(return_value=mock_transaction)
    mock_mongo.client.start_session.return_value = mock_session

    # Act
    with caplog.at_level(logging.INFO):
        await process_message(message, mock_repo, mock_mongo, mock_connection)

    # Assert
    assert "Success: sending email, message_id=fake_id" in caplog.text
    mock_send_email.assert_called_once()
    mock_repo.update_status_doc.assert_called_once_with("fake_id", "sent", mock_session)
    message.ack.assert_called_once()


@pytest.mark.asyncio
@patch("services.message.send_email")
async def test_process_message_not_published_attempts_lt_5(
        mock_send_email,
        mock_incoming_data,
        mock_repo,
        mock_connection,
        mock_mongo,
        mock_data,
        caplog
):
    """Tests email publishing failure when attempts less than five."""
    # Arrange
    message = AsyncMock()
    message.body = mock_incoming_data.encode()
    message.message_id = "fake_id"
    message.headers = {"x-retry-count": 2}
    message.nack = AsyncMock()

    mock_repo.get_doc = AsyncMock(side_effect=[
        None,
        {
            "email": "user@example.com",
            "subject": "reset password",
            "body": "click the link",
            "token": "fake_token",
            "status": "pending"
        }
    ])
    mock_repo.save_doc = AsyncMock()
    mock_send_email.side_effect = Exception()

    mock_session = AsyncMock()
    mock_transaction = AsyncMock()

    mock_transaction.__aenter__.return_value = None
    mock_transaction.__aexit__.return_value = None

    mock_session.start_transaction = Mock(return_value=mock_transaction)
    mock_mongo.client.start_session.return_value = mock_session

    channel = AsyncMock()
    mock_connection.channel = AsyncMock(return_value=channel)
    channel.default_exchange.publish.side_effect = Exception()

    # Act
    with caplog.at_level(logging.WARNING):
        await process_message(message, mock_repo, mock_mongo, mock_connection)

    # Assert
    assert "Failed retry to publish message, message_id=fake_id" in caplog.text
    mock_send_email.assert_called_once()
    mock_connection.channel.assert_called_once()
    channel.default_exchange.publish.assert_called_once()
    message.nack.assert_called_once_with(requeue=True)