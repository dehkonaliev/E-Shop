from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from .views import (
    ActivateAliasAPIView,
    ActivateAPIView,
    LegacyRegisterAPIView,
    LegacyRegisterSlashAPIView,
    LegacyVerifyCodeAPIView,
    LegacyVerifyCodeSlashAPIView,
    LoginAPIView,
    LogoutAPIView,
    ProfileAPIView,
    RegisterAPIView,
    VerifyCodeAPIView,
)

app_name = "auth"

urlpatterns = [
    path("register/", RegisterAPIView.as_view(), name="register"),
    path("temp-create", LegacyRegisterAPIView.as_view(), name="legacy-register"),
    path("temp-create/", LegacyRegisterSlashAPIView.as_view(), name="legacy-register-slash"),
    path("email-confirm", LegacyVerifyCodeAPIView.as_view(), name="legacy-email-confirm"),
    path("email-confirm/", LegacyVerifyCodeSlashAPIView.as_view(), name="legacy-email-confirm-slash"),
    path("email/confirm/", VerifyCodeAPIView.as_view(), name="email-confirm"),
    path("user-activation/", ActivateAPIView.as_view(), name="user-activation"),
    path("activate/", ActivateAliasAPIView.as_view(), name="activate"),
    path("login/", LoginAPIView.as_view(), name="login"),
    path("profile/", ProfileAPIView.as_view(), name="profile"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token-verify"),
    path("logout/", LogoutAPIView.as_view(), name="logout"),
]
