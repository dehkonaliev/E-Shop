from django.urls import path
from .views import TempUserCreateAPIView, VerifyCodeAPIView

urlpatterns = [
    path('temp-create', TempUserCreateAPIView.as_view()),
    path('email-confirm', VerifyCodeAPIView.as_view()),
]