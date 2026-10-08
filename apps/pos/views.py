from decimal import Decimal
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.common.viewsets import TenantModelViewSet
from .models import CashRegister, RegisterSession, RegisterStatus
from .serializers import CashRegisterSerializer, RegisterSessionSerializer


class CashRegisterViewSet(TenantModelViewSet):
    queryset = CashRegister.objects.select_related('store', 'current_cashier').all()
    serializer_class = CashRegisterSerializer
    filterset_fields = ['store', 'status']

    @action(detail=True, methods=['post'])
    def open_session(self, request, pk=None):
        register = self.get_object()
        if register.status == RegisterStatus.OPEN:
            return Response({'error': 'La caisse est déjà ouverte.'}, status=status.HTTP_400_BAD_REQUEST)

        opening_balance = Decimal(str(request.data.get('opening_balance', 0.0)))
        register.status = RegisterStatus.OPEN
        register.current_cashier = request.user
        register.opening_balance = opening_balance
        register.current_balance = opening_balance
        register.save()

        session = RegisterSession.objects.create(
            company=register.company,
            register=register,
            cashier=request.user,
            opening_balance=opening_balance
        )

        return Response(RegisterSessionSerializer(session).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def close_session(self, request, pk=None):
        register = self.get_object()
        if register.status == RegisterStatus.CLOSED:
            return Response({'error': 'La caisse est déjà fermée.'}, status=status.HTTP_400_BAD_REQUEST)

        closing_balance = Decimal(str(request.data.get('closing_balance', register.current_balance)))
        session = RegisterSession.objects.filter(
            company=register.company,
            register=register,
            is_closed=False
        ).order_by('-opened_at').first()

        if session:
            session.closed_at = timezone.now()
            session.closing_balance = closing_balance
            session.difference = closing_balance - register.current_balance
            session.is_closed = True
            session.save()

        register.status = RegisterStatus.CLOSED
        register.current_cashier = None
        register.save()

        return Response({'status': 'Session fermée', 'closing_balance': str(closing_balance)})


class RegisterSessionViewSet(TenantModelViewSet):
    queryset = RegisterSession.objects.select_related('register', 'cashier').all()
    serializer_class = RegisterSessionSerializer
    filterset_fields = ['register', 'cashier', 'is_closed']
