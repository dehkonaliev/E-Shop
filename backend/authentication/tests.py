import re
import smtplib
from unittest.mock import patch

from django.core import mail
from django.test import TransactionTestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from baseapp.services import issue_activation_token

from .models import CustomUser, SingUpCode, TempUser


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class AuthenticationFlowTests(APITestCase):
    def setUp(self):
        mail.outbox.clear()

    def test_registration_confirmation_activation_and_jwt_flow(self):
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse("auth:register"),
                {"email": "User@Example.com"},
                format="json",
            )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TempUser.objects.count(), 1)
        self.assertEqual(SingUpCode.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

        code_match = re.search(r"\b\d{6}\b", mail.outbox[0].body)
        self.assertIsNotNone(code_match)
        response = self.client.post(
            reverse("auth:email-confirm"),
            {
                "email": "user@example.com",
                "code": code_match.group(0),
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        activation_token = response.data["activation_token"]

        response = self.client.post(
            reverse("auth:user-activation"),
            {
                "token": activation_token,
                "username": "customer",
                "password": "StrongPass123!",
                "phone_number": "+998901234567",
                "age": 25,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        user = CustomUser.objects.get(email="user@example.com")
        self.assertTrue(user.is_active)
        self.assertTrue(user.check_password("StrongPass123!"))
        self.assertNotEqual(user.password, "StrongPass123!")

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        response = self.client.get(reverse("auth:profile"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["role"], CustomUser.Role.CUSTOMER)

        response = self.client.post(
            reverse("auth:login"),
            {
                "email": "USER@example.com",
                "password": "StrongPass123!",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_legacy_registration_and_confirmation_routes_work(self):
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse("auth:legacy-register"),
                {"email": "legacy@example.com"},
                format="json",
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        code_match = re.search(r"\b\d{6}\b", mail.outbox[0].body)
        response = self.client.post(
            reverse("auth:legacy-email-confirm"),
            {
                "email": "legacy@example.com",
                "code": code_match.group(0),
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        self.assertIn("activation_token", response.data)

    def test_activation_token_is_single_use(self):
        temp_user = TempUser.objects.create(email="single-use@example.com")
        with self.captureOnCommitCallbacks(execute=True):
            _, activation_token = issue_activation_token(
                temp_user,
                "https://example.com/activate?token={token}",
            )
        payload = {
            "token": activation_token,
            "username": "singleuser",
            "password": "StrongPass123!",
        }
        first_response = self.client.post(
            reverse("auth:user-activation"),
            payload,
            format="json",
        )
        second_response = self.client.post(
            reverse("auth:user-activation"),
            payload,
            format="json",
        )
        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second_response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_rejects_wrong_password(self):
        CustomUser.objects.create_user(
            username="existing",
            email="existing@example.com",
            password="StrongPass123!",
        )
        response = self.client.post(
            reverse("auth:login"),
            {
                "email": "existing@example.com",
                "password": "WrongPass123!",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_email_has_html_alternative(self):
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse("auth:register"),
                {"email": "html@example.com"},
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, ["html@example.com"])
        code_match = re.search(r"\b\d{6}\b", message.body)
        self.assertIsNotNone(code_match)
        self.assertEqual(len(message.alternatives), 1)
        content, mimetype = message.alternatives[0]
        self.assertEqual(mimetype, "text/html")
        self.assertIn(code_match.group(0), content)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class MailDeliveryFailureTests(TransactionTestCase):
    """The on_commit mail send must run inside the request, not after it."""

    def setUp(self):
        mail.outbox.clear()

    def test_registration_returns_503_when_smtp_delivery_fails(self):
        with patch("baseapp.mail.logger"), patch(
            "django.core.mail.backends.locmem.EmailBackend.send_messages",
            side_effect=smtplib.SMTPServerDisconnected("Connection closed"),
        ):
            response = self.client.post(
                reverse("auth:register"),
                {"email": "offline@example.com"},
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn("email", str(response.data).lower())
