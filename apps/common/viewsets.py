from rest_framework import viewsets
from .permissions import IsAuthenticatedAndInTenant


class TenantModelViewSet(viewsets.ModelViewSet):
    """
    Base viewset for all multi-tenant entities.
    - Restricts querysets strictly to the authenticated user's company.
    - Automatically injects user's company upon record creation.
    - Prevents cross-tenant data leaks.
    """
    permission_classes = [IsAuthenticatedAndInTenant]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not user or not user.is_authenticated:
            return qs.none()
        if user.is_superuser and not user.company_id:
            return qs
        return qs.filter(company_id=user.company_id)

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(company_id=user.company_id)
