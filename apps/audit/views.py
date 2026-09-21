from rest_framework import serializers, viewsets, permissions
from apps.common.viewsets import TenantModelViewSet
from apps.common.permissions import RolePermission
from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = AuditLog
        fields = ['id', 'company', 'action', 'resource_type', 'resource_id', 'user_email', 'ip_address', 'details', 'created_at']
        read_only_fields = fields


class AuditLogViewSet(TenantModelViewSet):
    """
    Read-only audit log endpoint for compliance and investigation.
    Restricted to ADMIN, MANAGER, and AUDITOR roles.
    """
    http_method_names = ['get', 'head', 'options']
    queryset = AuditLog.objects.select_related('user').all()
    serializer_class = AuditLogSerializer
    filterset_fields = ['action', 'resource_type']
    search_fields = ['resource_id', 'details']
    required_roles = ['ADMIN', 'MANAGER', 'AUDITOR']
    permission_classes = [TenantModelViewSet.permission_classes[0], RolePermission]
