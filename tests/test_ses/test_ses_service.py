from unittest.mock import patch, AsyncMock

import pytest

from ses.ses_service import send_email


@pytest.mark.asyncio
@patch("ses.ses_service.ses_session.client")
async def test_send_email_success(
        mock_ses_session
):
    # Arrange/Act
    mock_ses_client = AsyncMock()
    mock_ses_client.send_email.return_value = {"MessageId": "fake_id"}

    mock_ses_session.return_value.__aenter__.return_value = mock_ses_client

    message_id = await send_email(
        "from@example.com",
        "recipient@example.com",
        "subject",
        "text",
        "html"
    )

    # Assert
    assert message_id == "fake_id"
    mock_ses_client.send_email.assert_called_once()


@pytest.mark.asyncio
@patch("ses.ses_service.ses_session.client")
async def test_send_email_failure(
        mock_ses_session
):
    # Arrange/Act
    mock_ses_client = AsyncMock()
    mock_ses_client.send_email.side_effect = Exception("SES error")

    mock_ses_session.return_value.__aenter__.return_value = mock_ses_client

    with pytest.raises(Exception) as e:
        await send_email(
            "from@example.com",
            "recipient@example.com",
            "subject",
            "text",
            "html"
        )

    # Assert
    assert "SES error" in str(e.value)


@pytest.mark.asyncio
@patch("ses.ses_service.ses_session.client")
async def test_send_email_with_reply_tos(
        mock_ses_session
):
    # Arrange/Act
    mock_ses_client = AsyncMock()
    mock_ses_client.send_email.return_value = {"MessageId": "fake_id"}

    mock_ses_session.return_value.__aenter__.return_value = mock_ses_client

    reply_tos = ["reply@example.com"]

    message_id = await send_email(
        "from@example.com",
        "recipient@example.com",
        "subject",
        "text",
        "html",
        reply_tos=reply_tos
    )

    # Assert
    assert message_id == "fake_id"
    mock_ses_client.send_email.assert_called_once()
    args, kwargs = mock_ses_client.send_email.call_args
    assert kwargs["ReplyToAddresses"] == reply_tos