from rest_framework.permissions import BasePermission


class IsUser(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and not (request.user.is_staff or request.user.is_superuser))


class IsManager(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser))


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.is_superuser)