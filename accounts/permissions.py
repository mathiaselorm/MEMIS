from rest_framework import permissions
from django.contrib.auth import get_user_model

User = get_user_model()

class IsAdminUser(permissions.BasePermission):
    """
    Custom permission to allow only Admins and Superadmins to access specific views.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type in [User.UserType.ADMIN, User.UserType.SUPERADMIN]

class IsTechnicianUser(permissions.BasePermission):
    """
    Custom permission to allow only Technicians to access specific views.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == User.UserType.TECHNICIAN