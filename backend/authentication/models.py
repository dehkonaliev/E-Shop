from django.db import models
from baseapp.models import BaseModel
from django.contrib.auth.models import AbstractUser


class CustomUser(BaseModel, AbstractUser):
    phone_number = models.CharField(max_length=13, blank=True, null=True)
    age = models.PositiveIntegerField(blank=True, null=True)
    
    
    