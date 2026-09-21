from rest_framework import serializers
from .models import Partner


class PartnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partner
        fields = [
            'id', 'company', 'name', 'partner_type', 'email', 'phone',
            'address', 'tax_number', 'credit_limit', 'current_balance',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'company', 'current_balance', 'created_at', 'updated_at']
