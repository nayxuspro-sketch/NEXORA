from rest_framework import serializers
from .models import CashRegister, RegisterSession


class CashRegisterSerializer(serializers.ModelSerializer):
    store_name = serializers.CharField(source='store.name', read_only=True)
    cashier_name = serializers.CharField(source='current_cashier.email', read_only=True)

    class Meta:
        model = CashRegister
        fields = [
            'id', 'company', 'store', 'store_name', 'name', 'code',
            'status', 'current_cashier', 'cashier_name', 'opening_balance',
            'current_balance', 'created_at'
        ]
        read_only_fields = ['id', 'company', 'status', 'current_cashier', 'current_balance', 'created_at']


class RegisterSessionSerializer(serializers.ModelSerializer):
    cashier_name = serializers.CharField(source='cashier.email', read_only=True)
    register_name = serializers.CharField(source='register.name', read_only=True)

    class Meta:
        model = RegisterSession
        fields = [
            'id', 'company', 'register', 'register_name', 'cashier', 'cashier_name',
            'opened_at', 'closed_at', 'opening_balance', 'closing_balance',
            'cash_sales_total', 'difference', 'is_closed'
        ]
        read_only_fields = ['id', 'company', 'opened_at', 'closed_at', 'is_closed', 'difference']
