import secrets
from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from django.utils.crypto import salted_hmac

from authentication.models import SingUpCode, TempToken, TempUser

from .mail import send_template_mail

VERIFICATION_CODE_EXPIRY_MINUTES = 5
ACTIVATION_TOKEN_EXPIRY_MINUTES = 60


def verification_code_hash(email, code):
    return salted_hmac(
        "authentication.email-confirmation",
        code,
        secret=email.lower(),
    ).hexdigest()


def activation_token_hash(token):
    return salted_hmac(
        "authentication.user-activation",
        token,
        secret="activation",
    ).hexdigest()


def send_verification_code(temp_user):
    with transaction.atomic():
        locked_user = TempUser.objects.select_for_update().get(pk=temp_user.pk)
        SingUpCode.objects.filter(
            user=locked_user,
            is_used=False,
        ).update(is_used=True)
        code = f"{secrets.randbelow(1_000_000):06d}"
        code_object = SingUpCode.objects.create(
            user=locked_user,
            code=verification_code_hash(locked_user.email, code),
        )
    transaction.on_commit(
        lambda: send_template_mail(
            locked_user.email,
            "verification_code",
            "Confirm your E-Shop email",
            {
                "code": code,
                "expiry_minutes": VERIFICATION_CODE_EXPIRY_MINUTES,
            },
        )
    )
    return code_object


def issue_activation_token(temp_user, activation_url):
    with transaction.atomic():
        locked_user = TempUser.objects.select_for_update().get(pk=temp_user.pk)
        TempToken.objects.filter(user=locked_user, is_used=False).update(is_used=True)
        token = secrets.token_urlsafe(32)
        token_object = TempToken.objects.create(
            user=locked_user,
            token=activation_token_hash(token),
            expire_time=timezone.now()
            + timedelta(minutes=ACTIVATION_TOKEN_EXPIRY_MINUTES),
        )
    transaction.on_commit(
        lambda: send_template_mail(
            locked_user.email,
            "activation_token",
            "Activate your E-Shop account",
            {
                "token": token,
                "activation_url": activation_url.format(token=token),
                "expiry_minutes": ACTIVATION_TOKEN_EXPIRY_MINUTES,
            },
        )
    )
    return token_object, token
