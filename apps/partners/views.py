from apps.common.viewsets import TenantModelViewSet
from .models import Partner, PartnerType
from .serializers import PartnerSerializer


class PartnerViewSet(TenantModelViewSet):
    queryset = Partner.objects.all()
    serializer_class = PartnerSerializer
    search_fields = ['name', 'phone', 'email', 'tax_number']
    filterset_fields = ['partner_type', 'is_active']
    ordering_fields = ['name', 'current_balance', 'created_at']
