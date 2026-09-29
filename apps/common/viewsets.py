from rest_framework import viewsets
from .permissions import IsAuthenticatedAndInTenant


class TenantModelViewSet(viewsets.ModelViewSet):
    """
    Base viewset for all multi-tenant entities.
    - Restricts querysets strictly to the active company.
    - Automatically injects user's company upon record creation.
    - Prevents cross-tenant data leaks.
    """
    permission_classes = [IsAuthenticatedAndInTenant]

    def get_company(self):
        user = self.request.user
        if user and user.is_authenticated and getattr(user, 'company_id', None):
            return user.company
        from apps.companies.models import Company
        company = Company.objects.first()
        if not company:
            company = Company.objects.create(name="NEXORA BURKINA COMMERCIAL GROUP", currency="XOF")
        return company

    def get_queryset(self):
        qs = super().get_queryset()
        company = self.get_company()
        if company:
            return qs.filter(company=company)
        return qs

    def perform_create(self, serializer):
        company = self.get_company()
        serializer.save(company=company)
