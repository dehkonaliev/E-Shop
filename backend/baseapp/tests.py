import re
import smtplib
from unittest.mock import patch

from django.core import mail
from django.test import SimpleTestCase, override_settings

from .mail import MailDeliveryError, send_mail, send_template_mail


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class SendMailTests(SimpleTestCase):
    def setUp(self):
        mail.outbox.clear()

    def test_send_mail_sends_plain_text_only(self):
        send_mail("user@example.com", "Hello there", "Greetings")

        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.subject, "Greetings")
        self.assertEqual(message.body, "Hello there")
        self.assertEqual(message.to, ["user@example.com"])
        self.assertEqual(message.alternatives, [])

    def test_send_mail_attaches_html_alternative(self):
        send_mail(
            "user@example.com",
            "Plain body",
            "Greetings",
            html_message="<p>HTML body</p>",
        )

        message = mail.outbox[0]
        self.assertEqual(message.body, "Plain body")
        self.assertEqual(len(message.alternatives), 1)
        content, mimetype = message.alternatives[0]
        self.assertEqual(mimetype, "text/html")
        self.assertIn("HTML body", content)

    def test_send_mail_rejects_missing_recipient(self):
        with self.assertRaises(MailDeliveryError):
            send_mail("   ", "Hello there", "Greetings")

    def test_send_mail_wraps_smtp_errors(self):
        with patch("baseapp.mail.logger"), patch(
            "django.core.mail.backends.locmem.EmailBackend.send_messages",
            side_effect=smtplib.SMTPConnectError(421, "Service unavailable"),
        ):
            with self.assertRaises(MailDeliveryError):
                send_mail("user@example.com", "Hello there", "Greetings")

    def test_send_template_mail_renders_both_bodies(self):
        send_template_mail(
            "user@example.com",
            "verification_code",
            "Confirm your E-Shop email",
            {"code": "123456", "expiry_minutes": 5},
        )

        message = mail.outbox[0]
        self.assertEqual(message.subject, "Confirm your E-Shop email")
        self.assertEqual(re.search(r"\b\d{6}\b", message.body).group(0), "123456")
        self.assertIn("expires in 5 minutes", message.body)
        self.assertEqual(len(message.alternatives), 1)
        content, mimetype = message.alternatives[0]
        self.assertEqual(mimetype, "text/html")
        self.assertIn("123456", content)

    def test_send_template_mail_renders_activation_link(self):
        send_template_mail(
            "user@example.com",
            "activation_token",
            "Activate your E-Shop account",
            {
                "token": "abc123",
                "activation_url": "https://example.com/activate?token=abc123",
                "expiry_minutes": 60,
            },
        )

        message = mail.outbox[0]
        self.assertIn("abc123", message.body)
        self.assertIn("https://example.com/activate?token=abc123", message.body)
        html_content, _ = message.alternatives[0]
        self.assertIn("https://example.com/activate?token=abc123", html_content)
