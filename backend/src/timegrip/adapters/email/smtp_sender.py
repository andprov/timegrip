import logging
from email.message import EmailMessage
from email.utils import formataddr

import aiosmtplib

from timegrip.application.common.email_config import EmailConfig
from timegrip.application.outbox.email_sender_gateway import (
    EmailSenderGateway,
)

logger = logging.getLogger(__name__)


class SMTPEmailSender(EmailSenderGateway):
    def __init__(self, config: EmailConfig) -> None:
        self.config = config

    async def send(
        self,
        to_email: str,
        subject: str,
        body: str,
    ) -> None:
        message = EmailMessage()
        message["From"] = formataddr(
            (self.config.from_name, self.config.from_email),
        )
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content(body)

        await aiosmtplib.send(
            message,
            hostname=self.config.host,
            port=self.config.port,
            username=self.config.username,
            password=self.config.password,
            use_tls=self.config.use_tls,
        )
        logger.info(f"Send email | [to: {to_email}]")
