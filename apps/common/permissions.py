from rest_framework import permissions


class IsAuthenticatedAndInTenant(permissions.BasePermission):
    """
    Ensures user is authenticated and is bound to a valid active company/tenant.
    """
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_superuser:
            return True
        return bool(request.user.company_id and request.user.is_active)

    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_superuser:
            return True
        
        # If object has company attribute, verify multi-tenant isolation
        if hasattr(obj, 'company_id'):
            return obj.company_id == request.user.company_id
        if hasattr(obj, 'company'):
            return obj.company == request.user.company
        return True


class RolePermission(permissions.BasePermission):
    """
    Role-based access control.
    Views can define `required_roles = ['ADMIN', 'MANAGER', ...]`
    """
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_superuser:
            return True

        required_roles = getattr(view, 'required_roles', None)
        if not required_roles:
            return True

        user_role = getattr(request.user, 'role', None)
        return user_role in required_roles
