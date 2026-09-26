from drf_spectacular.utils import OpenApiTypes, extend_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    ActivationSerializer,
    LoginSerializer,
    LogoutSerializer,
    JWTResponseSerializer,
    ProfileSerializer,
    RegisterSerializer,
    UserSerializer,
    VerifyCodeSerializer,
)


def jwt_response(user):
    refresh = RefreshToken.for_user(user)
    return {
        "user": UserSerializer(user).data,
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


class RegisterAPIView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "register"

    @extend_schema(
        tags=["Authentication"],
        operation_id="auth_register",
        request=RegisterSerializer,
        responses={201: OpenApiTypes.OBJECT},
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        temp_user = serializer.save()
        return Response(
            {
                "message": "Verification code sent to the email.",
                "data": {"email": temp_user.email},
            },
            status=status.HTTP_201_CREATED,
        )


class LegacyRegisterAPIView(RegisterAPIView):
    @extend_schema(
        tags=["Authentication"],
        operation_id="auth_legacy_register",
        request=RegisterSerializer,
        responses={200: OpenApiTypes.OBJECT},
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        temp_user = serializer.save()
        return Response(
            {
                "message": "Code sent to the email",
                "data": {"email": temp_user.email},
            }
        )


class LegacyRegisterSlashAPIView(LegacyRegisterAPIView):
    @extend_schema(
        tags=["Authentication"],
        operation_id="auth_legacy_register_slash",
        request=RegisterSerializer,
        responses={200: OpenApiTypes.OBJECT},
    )
    def post(self, request):
        return super().post(request)


class VerifyCodeAPIView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "email_confirm"

    @extend_schema(
        tags=["Authentication"],
        operation_id="auth_email_confirm",
        request=VerifyCodeSerializer,
        responses={200: VerifyCodeSerializer},
    )
    def post(self, request):
        serializer = VerifyCodeSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class LegacyVerifyCodeAPIView(VerifyCodeAPIView):
    @extend_schema(
        tags=["Authentication"],
        operation_id="auth_legacy_email_confirm",
        request=VerifyCodeSerializer,
        responses={200: VerifyCodeSerializer},
    )
    def post(self, request):
        return super().post(request)


class LegacyVerifyCodeSlashAPIView(VerifyCodeAPIView):
    @extend_schema(
        tags=["Authentication"],
        operation_id="auth_legacy_email_confirm_slash",
        request=VerifyCodeSerializer,
        responses={200: VerifyCodeSerializer},
    )
    def post(self, request):
        return super().post(request)


class ActivateAPIView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "user_activation"

    @extend_schema(
        tags=["Authentication"],
        operation_id="auth_user_activation",
        request=ActivationSerializer,
        responses={201: JWTResponseSerializer},
    )
    def post(self, request):
        serializer = ActivationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(jwt_response(user), status=status.HTTP_201_CREATED)


class ActivateAliasAPIView(ActivateAPIView):
    @extend_schema(
        tags=["Authentication"],
        operation_id="auth_activate",
        request=ActivationSerializer,
        responses={201: JWTResponseSerializer},
    )
    def post(self, request):
        return super().post(request)


class LoginAPIView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "login"

    @extend_schema(
        tags=["Authentication"],
        request=LoginSerializer,
        responses={200: JWTResponseSerializer},
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return Response(jwt_response(serializer.validated_data["user"]))


class ProfileAPIView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileSerializer

    def get_object(self):
        return self.request.user

    @extend_schema(
        tags=["Authentication"],
        responses={200: ProfileSerializer},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        tags=["Authentication"],
        request=ProfileSerializer,
        responses={200: ProfileSerializer},
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Authentication"],
        request=LogoutSerializer,
        responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT},
    )
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            token = RefreshToken(serializer.validated_data["refresh"])
            if str(token["user_id"]) != str(request.user.pk):
                raise ValidationError(
                    {"detail": "This refresh token belongs to another user."}
                )
            token.blacklist()
        except TokenError as exc:
            raise ValidationError({"detail": "Invalid refresh token."}) from exc
        return Response({"message": "Logged out successfully."})
