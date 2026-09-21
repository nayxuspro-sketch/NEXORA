from rest_framework import viewsets, permissions
from .models import Company
from .serializers import CompanySerializer


class CompanyViewSet(viewsets.ModelViewSet):
    """
    CRUD on Companies.
    Regular users only see their own company; superusers can see all.
    """
    serializer_class = CompanySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Company.objects.none()
        if user.is_superuser:
            return Company.objects.all()
        return Company.objects.filter(id=user.company_id)
