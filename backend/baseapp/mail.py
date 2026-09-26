from django.conf import settings
from django.core.mail import send_mail as django_send_mail


def send_mail(email, message, subject="E-Shop notification"):
    return django_send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )
