from rest_framework import serializers
from .models import AutomationRule, AutomationLog


class AutomationRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomationRule
        fields = [
            'id', 'company', 'name', 'description', 'trigger_type',
            'action_type', 'parameters', 'is_active', 'last_triggered_at',
            'execution_count', 'created_at'
        ]
        read_only_fields = ['id', 'company', 'last_triggered_at', 'execution_count', 'created_at']


class AutomationLogSerializer(serializers.ModelSerializer):
    rule_name = serializers.CharField(source='rule.name', read_only=True)

    class Meta:
        model = AutomationLog
        fields = ['id', 'company', 'rule', 'rule_name', 'executed_at', 'status', 'details']
        read_only_fields = fields
