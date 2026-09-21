from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.common.viewsets import TenantModelViewSet
from apps.common.permissions import IsAuthenticatedAndInTenant
from .models import AutomationRule, AutomationLog
from .serializers import AutomationRuleSerializer, AutomationLogSerializer
from .automation import AutomationEngine
from .service import AIAssistantService


class AutomationRuleViewSet(TenantModelViewSet):
    queryset = AutomationRule.objects.all()
    serializer_class = AutomationRuleSerializer
    filterset_fields = ['trigger_type', 'action_type', 'is_active']
    search_fields = ['name', 'description']

    @action(detail=False, methods=['post'])
    def trigger_engine(self, request):
        """
        Manually trigger evaluation of active automation rules for the tenant.
        """
        company = getattr(request.user, 'company', None)
        if not company:
            from apps.companies.models import Company
            company = Company.objects.first()
        results = AutomationEngine.evaluate_rules_for_company(company, user=request.user)
        return Response({
            'status': 'success',
            'message': f"{len(results)} règle(s) évaluée(s).",
            'executions': results
        })


class AutomationLogViewSet(TenantModelViewSet):
    http_method_names = ['get', 'head', 'options']
    queryset = AutomationLog.objects.select_related('rule').all()
    serializer_class = AutomationLogSerializer
    filterset_fields = ['rule', 'status']


class AIChatAssistantView(APIView):
    """
    Conversational AI Assistant Endpoint.
    Understands operational questions, enforces RBAC, and provides data-driven explications.
    """
    permission_classes = [IsAuthenticatedAndInTenant]

    def post(self, request):
        question = request.data.get('question', '').strip()
        if not question:
            return Response(
                {'error': 'Veuillez saisir une question pour l\'assistant.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        company = getattr(request.user, 'company', None)
        if not company:
            from apps.companies.models import Company
            company = Company.objects.first()

        response_payload = AIAssistantService.process_query(
            query=question,
            user=request.user,
            company=company
        )

        return Response(response_payload)
