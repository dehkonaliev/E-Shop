from django.db import models
from baseapp.models import BaseModel
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta
import secrets

class TempUser(BaseModel):
    email = models.EmailField()
    
    def __str__(self):
        return self.email
    
class SingUpCode(BaseModel):
    user = models.ForeignKey(TempUser, on_delete=models.CASCADE, related_name='signup_codes')
    code = models.CharField(max_length=6)
    is_used = models.BooleanField(default=False)
    expire_time = models.DateTimeField()
    
    def __str__(self):
        return self.user.email
    
    def save(self, *args, **kwargs):
        if not self.expire_time:
            self.expire_time = timezone.now() + timedelta(minutes=5)
        return super().save()
    
class TempToken(BaseModel):
    user = models.ForeignKey(TempUser, on_delete=models.CASCADE, related_name='temp_tokens')
    token = models.CharField(max_length=64)
    expire_time = models.DateTimeField(null=True)
    is_used = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(32)
            
        if not self.expire_time:
            self.expire_time = timezone.now() + timedelta(minutes=60)
        return super().save()

class CustomUser(BaseModel, AbstractUser):
    phone_number = models.CharField(max_length=13, blank=True, null=True)
    age = models.PositiveIntegerField(blank=True, null=True)
    
    
    