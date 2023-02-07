"""Module with function that sends plain text email from the sender to any receiver."""
from email.message import EmailMessage
import os
from smtplib import SMTP as SMTPServer
from ssl import create_default_context
from typing import Callable, List, Optional

from get_logger import get_logger

SENDER_ADDRESS: str = os.environ["SENDER_ADDRESS"]
SENDER_PASSWORD: str = os.environ["SENDER_PASSWORD"]

logger = get_logger(__file__)


def send_email(
    to_addresses: List[str],
    subject: str,
    body: str,
    is_html: bool = False,
    formatter: Optional[Callable[[str, str], str]] = None,
) -> None:
    """
    Sends the same plain text message to all given recipients.

    Args:
        to_addresses: the recipient email addresses
        subject: subject line of the email
        body: main message text of the email
        is_html: True if body string is html, False if it is plain text
        formatter: optional function that formats the message based on the recipient.
            If given, the actual body of the message is formatter(body, recipient),
            where recipient is the specific to_address being messaged.
    """
    if not to_addresses:
        return
    body = body.encode("ascii", "ignore").decode("ascii")
    context = create_default_context()
    subtype: str = "html" if is_html else "plain"
    with SMTPServer("smtp.gmail.com", port=587) as server:
        server.starttls(context=context)
        server.login(SENDER_ADDRESS, SENDER_PASSWORD)
        for to_address in to_addresses:
            logger.info(f'Sending email to {to_address} with subject line "{subject}".')
            message: EmailMessage = EmailMessage()
            message["Subject"] = subject
            message["From"] = SENDER_ADDRESS
            message["To"] = to_address
            message.set_content(
                body if formatter is None else formatter(body, to_address), subtype
            )
            server.send_message(message)

    return
