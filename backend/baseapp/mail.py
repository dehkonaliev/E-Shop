import logging
import smtplib

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


class MailDeliveryError(Exception):
    """Raised when the SMTP backend fails to hand off a message."""


def send_mail(email, message, subject="E-Shop notification", html_message=None):
    recipients = [address.strip() for address in [email] if address and address.strip()]
    if not recipients:
        raise MailDeliveryError("No recipient address was provided.")

    mail = EmailMultiAlternatives(
        subject=subject,
        body=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=recipients,
    )
    if html_message:
        mail.attach_alternative(html_message, "text/html")
    try:
        return mail.send(fail_silently=False)
    except (smtplib.SMTPException, OSError) as exc:
        logger.exception(
            "SMTP delivery failed for subject %r to %s",
            subject,
            recipients[0],
        )
        raise MailDeliveryError(
            f"Could not deliver email to {recipients[0]}: {exc}"
        ) from exc


def send_template_mail(email, template, subject, context=None):
    context = {"subject": subject, **(context or {})}
    return send_mail(
        email,
        render_to_string(f"email/{template}.txt", context),
        subject,
        html_message=render_to_string(f"email/{template}.html", context),
    )
