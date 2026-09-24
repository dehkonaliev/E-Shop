from authentication.models import SingUpCode
from .mail import send_mail
import random

def send_verification_code(temp_user):
    code = str(random.randint(100000, 999999))
    code_obj = SingUpCode.objects.create(code=code, user=temp_user)
    send_mail(temp_user.email, code)
    
    return code_obj
    