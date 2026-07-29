from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

LOG = logging.getLogger(__name__)


def send_email(*, to: list[str], subject: str, body: str) -> bool:
    recipients = [email.strip() for email in to if email and email.strip()]
    if not recipients:
        return False
    if not settings.smtp_username or not settings.smtp_password:
        LOG.warning("SMTP nao configurado; e-mail nao enviado: %s", subject)
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
    message["To"] = ", ".join(recipients)
    message.set_content(body)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
            smtp.starttls()
            smtp.login(settings.smtp_username, settings.smtp_password)
            smtp.send_message(message)
    except Exception:
        LOG.exception("Falha ao enviar e-mail: %s", subject)
        return False
    return True
