from django.db import models
from baseapp.models import BaseModel
from django.contrib.auth.models import AbstractUser

class TempUser(BaseModel):
    email = models.EmailField()
    
    def __str__(self):
        return self.email
    
class SingUpCode(BaseModel):
    user = models.ForeignKey(TempUser, on_delete=models.CASCADE, related_name='signup_code')
    code = models.CharField(max_length=6)
    
    def __str__(self):
        return self.user

class CustomUser(BaseModel, AbstractUser):
    phone_number = models.CharField(max_length=13, blank=True, null=True)
    age = models.PositiveIntegerField(blank=True, null=True)
    
    
    