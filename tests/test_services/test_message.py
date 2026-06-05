"""Provides unit tests for message processing logic  and error handling."""
import logging
from unittest.mock import patch, AsyncMock, MagicMock

import pytest

from services.message import process_message, process_dlq_message


@pytest.mark.asyncio
@patch("services.message.send_email")
async def test_process_message_success_message_in_db(
        mock_send_email,
        mock_incoming_data,
        mock_repo
):
    """Tests successful processing of a message already stored in the database."""
    # Arrange
    mock_repo.get_doc = AsyncMock(return_value=mock_incoming_data)
    message = AsyncMock()
    message.body = mock_incoming_data.encode()
    message.ack = AsyncMock()
    mock_repo.get_doc = AsyncMock(return_value={
        "email": "user@example.com",
        "subject": "reset password",
        "body": "click the link",
        "token": "fake_token"
    })
    mock_repo.delete_doc = AsyncMock()

    # Act
    await process_message(mock_incoming_data, message, mock_repo)

    # Assert
    mock_send_email.assert_called_once()
    message.ack.assert_called_once()
    mock_repo.delete_doc.assert_called_once_with("fake_token")


@pytest.mark.asyncio
@patch("services.message.IncomingResetPasswordMessage.model_validate_json")
@patch("services.message.send_email")
async def test_process_message_invalid_body(
        mock_send_email,
        mock_validate_incoming_data,
        mock_repo,
        caplog
):
    """Tests that incoming message body is invalid."""
    # Arrange
    raw_body = "invalid body"
    mock_validate_incoming_data.side_effect = Exception()
    message = AsyncMock()
    message.ack = AsyncMock()

    # Act
    with caplog.at_level(logging.ERROR):
        await process_message(raw_body, message, mock_repo)

    # Assert
    assert "Invalid body message" in caplog.text
    mock_send_email.assert_not_called()
    message.ack.assert_called_once()


@pytest.mark.asyncio
@patch("services.message.send_email")
async def test_process_message_not_send_attempts_lt_5(
        mock_send_email,
        mock_incoming_data,
        mock_repo,
        caplog
):
    """Tests email sending failure when attempts less than five."""
    # Arrange
    mock_repo.get_doc = AsyncMock(return_value={
        "email": "user@example.com",
        "subject": "reset password",
        "body": "click the link",
        "token": "fake_token",
        "attempts": 2
    })
    message = AsyncMock()
    mock_send_email.side_effect = Exception()
    mock_repo.increase_attempts = AsyncMock()
    mock_repo.update_status_doc = AsyncMock()
    message.nack = AsyncMock()

    # Act
    with caplog.at_level(logging.ERROR):
        await process_message(mock_incoming_data, message, mock_repo)

    # Assert
    assert "Error: failed sending email" in caplog.text
    mock_send_email.assert_called_once()
    mock_repo.increase_attempts.assert_called_once_with("fake_token")
    mock_repo.update_status_doc.assert_called_once_with("fake_token", "failed")
    message.nack.assert_called_once_with(requeue=True)


@pytest.mark.asyncio
@patch("services.message.send_email")
async def test_process_message_not_send_attempts_ge_5(
        mock_send_email,
        mock_incoming_data,
        mock_repo,
        caplog
):
    """Tests email sending failure when attempts greater than or equal to five."""
    # Arrange
    mock_repo.get_doc = AsyncMock(return_value={
        "email": "user@example.com",
        "subject": "reset password",
        "body": "click the link",
        "token": "fake_token",
        "attempts": 5
    })
    message = AsyncMock()
    mock_send_email.side_effect = Exception()
    mock_repo.increase_attempts = AsyncMock()
    mock_repo.update_status_doc = AsyncMock()
    message.nack = AsyncMock()

    # Act
    with caplog.at_level(logging.ERROR):
        await process_message(mock_incoming_data, message, mock_repo)

    # Assert
    assert "Error: failed sending email" in caplog.text
    mock_send_email.assert_called_once()
    mock_repo.increase_attempts.assert_called_once_with("fake_token")
    mock_repo.update_status_doc.assert_called_once_with("fake_token", "dlq")
    message.nack.assert_called_once_with(requeue=False)


@pytest.mark.asyncio
@patch("services.message.send_email")
async def test_process_message_general_exception(
        mock_send_email,
        mock_incoming_data,
        mock_repo,
        caplog
):
    """Tests the general exception handling."""
    # Arrange
    mock_repo.get_doc = AsyncMock(return_value={
        "email": "user@example.com",
        "subject": "reset password",
        "body": "click the link",
        "token": "fake_token",
        "attempts": 5
    })
    message = AsyncMock()
    mock_send_email.side_effect = Exception()
    mock_repo.increase_attempts = AsyncMock(side_effect=Exception())
    message.nack = AsyncMock()

    # Act
    with caplog.at_level(logging.CRITICAL):
        await process_message(mock_incoming_data, message, mock_repo)

    # Assert
    assert "Internal error in exception handler" in caplog.text
    message.nack.assert_called_once_with(requeue=True)


@pytest.mark.asyncio
@patch("services.message.IncomingResetPasswordMessage.model_validate_json")
@patch("services.message.send_email")
async def test_process_message_save_new_doc(
        mock_send_email,
        mock_validate_data,
        mock_incoming_data,
        mock_repo,
):
    """Tests saving a document when email sending is the first time."""
    # Arrange
    mock_validate_data.return_value = MagicMock(
        token="fake_token",
        email="user@example.com",
        subject="reset password",
        body="click the link",
        datetime="2024-01-01T00:00:00"
    )
    mock_repo.get_doc = AsyncMock(side_effect=[
        None,
        {
            "email": "user@example.com",
            "subject": "reset password",
            "body": "click the link",
            "token": "fake_token"
        }
    ])
    message = AsyncMock()
    mock_repo.save_doc = AsyncMock()
    mock_repo.delete_doc = AsyncMock()
    message.ack = AsyncMock()

    # Act
    await process_message(mock_incoming_data, message, mock_repo)

    # Assert
    mock_repo.save_doc.assert_called_once()
    mock_send_email.assert_called_once()
    mock_repo.delete_doc.assert_called_once_with("fake_token")
    message.ack.assert_called_once()


@pytest.mark.asyncio
@patch("services.message.IncomingResetPasswordMessage.model_validate_json")
@patch("services.message.send_email")
async def test_process_message_not_save_new_doc(
        mock_send_email,
        mock_validate_data,
        mock_incoming_data,
        mock_repo,
        caplog
):
    """Tests that a document saving fails when email sending is the first time."""
    # Arrange
    mock_validate_data.return_value = MagicMock(
        token="fake_token",
        email="user@example.com",
        subject="reset password",
        body="click the link",
        datetime="2024-01-01T00:00:00"
    )
    mock_repo.get_doc = AsyncMock(return_value=None)
    message = AsyncMock()
    mock_repo.save_doc = AsyncMock(side_effect=Exception())
    message.nack = AsyncMock()

    # Act
    with caplog.at_level(logging.ERROR):
        await process_message(mock_incoming_data, message, mock_repo)

    # Assert
    assert "Failed to save message into the database" in caplog.text
    mock_repo.save_doc.assert_called_once()
    mock_send_email.assert_not_called()
    message.nack.assert_called_once_with(requeue=True)


@pytest.mark.asyncio
@patch("services.message.send_email")
async def test_process_message_not_send_not_get_doc(
        mock_send_email,
        mock_incoming_data,
        mock_repo,
        caplog
):
    """Tests that email sending and/or document saving fail."""
    # Arrange
    mock_repo.get_doc = AsyncMock(return_value={
        "email": "user@example.com",
        "subject": "reset password",
        "body": "click the link",
        "token": "fake_token",
        "attempts": 2
    })
    message = AsyncMock()
    mock_send_email.side_effect = Exception()
    mock_repo.get_doc = AsyncMock(return_value=None)
    message.nack = AsyncMock()

    # Act
    with caplog.at_level(logging.ERROR):
        await process_message(mock_incoming_data, message, mock_repo)

    # Assert
    assert "Doc is not found in DB" in caplog.text
    mock_send_email.assert_not_called()
    message.nack.assert_called_once_with(requeue=False)


@pytest.mark.asyncio
async def test_process_dlq_message_success(caplog):
    """Tests that DLQ message acknowledge succeeds."""
    # Arrange
    message = AsyncMock()
    message.ack = AsyncMock()

    # Act
    with caplog.at_level(logging.WARNING):
        await process_dlq_message(message)

    # Assert
    assert "DLQ message was acknowledged" in caplog.text
    message.ack.assert_called_once()