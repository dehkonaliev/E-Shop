from urllib.parse import urlencode

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from baseapp.services import (
    activation_token_hash,
    issue_activation_token,
    send_verification_code,
    verification_code_hash,
)

from .models import CustomUser, SingUpCode, TempToken, TempUser


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)

    def validate_email(self, value):
        email = value.strip().lower()
        if CustomUser.objects.filter(email=email).exists():
            raise serializers.ValidationError("This email is already registered.")
        return email

    def create(self, validated_data):
        temp_user, _ = TempUser.objects.get_or_create(email=validated_data["email"])
        send_verification_code(temp_user)
        return temp_user


class VerifyCodeSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)
    code = serializers.CharField(max_length=6, min_length=6, write_only=True)

    def validate_email(self, value):
        return value.strip().lower()

    def create(self, validated_data):
        with transaction.atomic():
            temp_user = (
                TempUser.objects.select_for_update()
                .filter(email=validated_data["email"])
                .first()
            )
            if temp_user is None:
                raise serializers.ValidationError(
                    {"email": "Invalid email or code."}
                )
            code_object = (
                SingUpCode.objects.select_for_update()
                .filter(
                    user=temp_user,
                    code=verification_code_hash(
                        temp_user.email,
                        validated_data["code"],
                    ),
                    is_used=False,
                    expire_time__gt=timezone.now(),
                )
                .first()
            )
            if code_object is None:
                raise serializers.ValidationError(
                    {"code": "Invalid or expired code."}
                )
            code_object.is_used = True
            code_object.save(update_fields=["is_used", "updated_at"])
            request = self.context.get("request")
            if request is None:
                raise serializers.ValidationError("Request context is required.")
            activation_url = request.build_absolute_uri(
                f'{reverse("auth:user-activation")}?{urlencode({"token": "TOKEN_PLACEHOLDER"})}'
            )
            _, activation_token = issue_activation_token(
                temp_user,
                activation_url.replace("TOKEN_PLACEHOLDER", "{token}"),
            )
        activation_url = activation_url.replace("{token}", activation_token)
        return {
            "email": temp_user.email,
            "token": activation_token,
            "activation_token": activation_token,
        }

    def to_representation(self, instance):
        return {
            "message": "Email confirmed.",
            "email": instance["email"],
            "token": instance["token"],
            "activation_token": instance["activation_token"],
            "activation_required": True,
        }


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            "id",
            "uuid",
            "username",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "age",
            "role",
            "is_staff",
        ]
        read_only_fields = ["id", "uuid", "role", "is_staff"]


class JWTResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()


class ActivationSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=128, write_only=True)
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(
        max_length=128,
        min_length=8,
        write_only=True,
        style={"input_type": "password"},
    )
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    age = serializers.IntegerField(required=False, min_value=0, max_value=120)

    def validate_username(self, value):
        username = value.strip()
        if CustomUser.objects.filter(username__iexact=username).exists():
            raise serializers.ValidationError("This username is already taken.")
        return username

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        raw_token = validated_data["token"]
        with transaction.atomic():
            token_object = (
                TempToken.objects.select_for_update()
                .select_related("user")
                .filter(
                    token=activation_token_hash(raw_token),
                    is_used=False,
                    expire_time__gt=timezone.now(),
                )
                .first()
            )
            if token_object is None:
                raise serializers.ValidationError(
                    {"token": "Invalid or expired activation token."}
                )
            temp_user = token_object.user
            if CustomUser.objects.filter(email=temp_user.email).exists():
                raise serializers.ValidationError(
                    {"email": "This email is already registered."}
                )
            user = CustomUser(
                username=validated_data["username"],
                email=temp_user.email,
                first_name=validated_data.get("first_name", ""),
                last_name=validated_data.get("last_name", ""),
                phone_number=validated_data.get("phone_number") or None,
                age=validated_data.get("age"),
                role=CustomUser.Role.CUSTOMER,
                is_active=True,
            )
            user.set_password(validated_data["password"])
            user.save()
            token_object.is_used = True
            token_object.save(update_fields=["is_used", "updated_at"])
            temp_user.delete()
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(max_length=128, write_only=True)

    def validate_email(self, value):
        return value.strip().lower()

    def validate(self, attrs):
        user = CustomUser.objects.filter(email=attrs["email"]).first()
        authenticated_user = authenticate(
            request=self.context.get("request"),
            username=user.username if user else None,
            password=attrs["password"],
        )
        if user is None or authenticated_user is None or not user.is_active:
            raise serializers.ValidationError("Invalid email or password.")
        attrs["user"] = authenticated_user
        return attrs


class ProfileSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields
        read_only_fields = ["id", "uuid", "email", "role"]


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(write_only=True)
