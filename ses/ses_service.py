"""
This file provides an async function for sending emails through Amazon SES.
It creates the SES client and sends messages using the given data.
"""
import aioboto3
from botocore.exceptions import ClientError

from core.config import settings

ses_session = aioboto3.Session(
    aws_access_key_id=settings.aws_access_key_id,
    aws_secret_access_key=settings.aws_secret_access_key,
    region_name=settings.aws_region,
)

async def send_email(source, destination, subject, text, html, reply_tos=None) -> str:
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

    try:
        async with ses_session.client("ses") as ses:
            response = await ses.send_email(**send_args)
            return response["MessageId"]
    except ClientError:
        raise