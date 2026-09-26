from rest_framework.permissions import BasePermission

from .models import CustomUser


class IsAdminRole(BasePermission):
    message = "Administrator permission is required."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (user.is_staff or user.role == CustomUser.Role.ADMIN)
        )
