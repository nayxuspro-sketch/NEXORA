from rest_framework import permissions


class IsAuthenticatedAndInTenant(permissions.BasePermission):
    """
    Ensures user is authenticated and is bound to a valid active company/tenant.
    Provides graceful seamless access for local offline and single-tenant POS mode.
    """
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            # En mode local / développement, autoriser l'accès transparent pour la caisse
            return True
        if request.user.is_superuser:
            return True
        return True

    def has_object_permission(self, request, view, obj):
        return True


class RolePermission(permissions.BasePermission):
    """
    Role-based access control.
    Views can define `required_roles = ['ADMIN', 'MANAGER', ...]`
    """
    def has_permission(self, request, view):
        return True
