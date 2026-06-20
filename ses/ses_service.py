"""
This file provides an async function for sending emails through Amazon SES.
It creates the SES client and sends messages using the given data.
"""
import logging

import aioboto3

from core.config import settings

logger = logging.getLogger(__name__)

ses_session = aioboto3.Session(
    aws_access_key_id=settings.aws_access_key_id,
    aws_secret_access_key=settings.aws_secret_access_key,
    region_name=settings.aws_region,
)

async def send_email(
        source: str,
        destination: str,
        subject: str,
        text: str,
        html: str,
        reply_tos:  list[str] | None = None
) -> str:
    """
    Sends an email.

    Args:
        source: Source email address used as the sender.
        destination: Recipient email address.
        subject: Subject line of the email.
        text: Plain‑text version of the email body.
        html: HTML version of the email body.
        reply_tos: Optional list of reply‑to addresses.
    Returns:
        str: The SES message ID assigned to the sent email.
    """

    send_args = {
        "Source": source,
        "Destination": {"ToAddresses": [destination]},
        "Message": {
            "Subject": {"Data": subject},
            "Body": {
                "Text": {"Data": text},
                "Html": {"Data": html}
            },
        },
    }

    if reply_tos:
        send_args["ReplyToAddresses"] = reply_tos

    logger.info(f"Start: sending email to {destination}")
    async with ses_session.client("ses") as ses:
        response = await ses.send_email(**send_args)
        logger.info(f"Success: sending email to {destination}, message_id={response['MessageId']}")
        return response["MessageId"]