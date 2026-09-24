from django.contrib import admin
from .models import CustomUser, TempUser, SingUpCode, TempToken

admin.site.register(CustomUser)
admin.site.register(SingUpCode)
admin.site.register(TempUser)
admin.site.register(TempToken)
