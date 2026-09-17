import logging

from timegrip.application.outbox.email_sender_gateway import (
    EmailSenderGateway,
)

logger = logging.getLogger(__name__)


class ConsoleEmailSender(EmailSenderGateway):
    async def send(
        self,
        to_email: str,
        subject: str,
        body: str,
    ) -> None:
        logger.info(
            f"[console-email] To: {to_email} | Subject: {subject}\n{body}",
        )
