from rest_framework import serializers
from .models import CustomUser, TempUser, SingUpCode, TempToken
from baseapp.services import send_verification_code
from django.utils import timezone


class TempUserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TempUser
        fields = ['email']
        
    def create(self, validated_data):
        email = validated_data['email']
        temp_user = TempUser.objects.filter(email=email).first()
        if temp_user:
            if SingUpCode.objects.filter(user=temp_user, expire_time__gt=timezone.now()).exists():
                raise serializers.ValidationError("Wait until prior expiry-code expires")
            send_verification_code(temp_user)
            return temp_user
        
        temp_user = TempUser.objects.create(email=email)
        send_verification_code(temp_user)
        return temp_user
    
class VerifyCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        email = attrs['email']
        code = attrs['code']
        
        temp_user = TempUser.objects.filter(email=email).first()
        if not temp_user:
            raise serializers.ValidationError("User not found")
        code_obj = temp_user.signup_codes.all().filter(code=code, expire_time__gt=timezone.now(), is_used=False).first()
        if not code_obj:
            raise serializers.ValidationError("Invalid code")
        
        code_obj.is_used = True
        code_obj.save()
        
        token = TempToken.objects.create(user=temp_user)
        attrs['token'] = token.token
        
        return attrs
    
    def to_representation(self, instance):
        return {
            "message": "Email confirmed!",
            'email': instance['email'],
            'token': instance['token']
        }
        
        

