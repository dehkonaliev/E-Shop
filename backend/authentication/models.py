from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from baseapp.models import BaseModel


class TempUser(BaseModel):
    email = models.EmailField(unique=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        self.email = self.email.strip().lower()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.email


class SingUpCode(BaseModel):
    user = models.ForeignKey(
        TempUser,
        on_delete=models.CASCADE,
        related_name="signup_codes",
    )
    code = models.CharField(max_length=128)
    is_used = models.BooleanField(default=False)
    expire_time = models.DateTimeField()

    class Meta:
        indexes = [
            models.Index(fields=["user", "is_used", "expire_time"]),
        ]
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.expire_time:
            self.expire_time = timezone.now() + timedelta(minutes=5)
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.user.email


class TempToken(BaseModel):
    user = models.ForeignKey(
        TempUser,
        on_delete=models.CASCADE,
        related_name="temp_tokens",
    )
    token = models.CharField(max_length=64, unique=True)
    expire_time = models.DateTimeField(null=True)
    is_used = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["user", "is_used", "expire_time"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"Activation token for {self.user.email}"


class CustomUser(BaseModel, AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        CUSTOMER = "customer", "Customer"

    email = models.EmailField(unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    age = models.PositiveIntegerField(blank=True, null=True)
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.CUSTOMER,
    )

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.strip().lower()
        if self.is_staff or self.is_superuser:
            self.role = self.Role.ADMIN
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.email or self.username
