from django.db import OperationalError
from rest_framework.response import Response
from rest_framework.views import exception_handler

from .mail import MailDeliveryError


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        return response
    if isinstance(exc, MailDeliveryError):
        return Response(
            {"detail": "We could not send the email. Please try again."},
            status=503,
        )
    if isinstance(exc, OperationalError):
        return Response(
            {"detail": "Database is busy. Please retry the request."},
            status=409,
        )
    return None
