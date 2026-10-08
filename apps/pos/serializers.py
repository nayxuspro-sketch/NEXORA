from rest_framework import serializers
from .models import CashRegister, RegisterSession


class CashRegisterSerializer(serializers.ModelSerializer):
    store_name = serializers.CharField(source='store.name', read_only=True)
    store_logo = serializers.CharField(source='store.logo', read_only=True)
    cashier_name = serializers.CharField(source='current_cashier.email', read_only=True)

    class Meta:
        model = CashRegister
        fields = [
            'id', 'company', 'store', 'store_name', 'store_logo', 'name', 'code',
            'status', 'current_cashier', 'cashier_name', 'opening_balance',
            'current_balance', 'created_at'
        ]
        read_only_fields = ['id', 'company', 'status', 'current_cashier', 'current_balance', 'created_at']

    def validate_store(self, magasin):
        # Une caisse doit etre rattachee a un magasin de SON entreprise.
        # Sans ce controle, une caisse pouvait viser le magasin d'une autre
        # entreprise : chaque vente passait alors ce magasin etranger au
        # serveur, qui la refusait (« Magasin introuvable dans votre
        # entreprise »). La compagnie etant posee par la vue, elle n'est pas
        # encore connue ici : on retombe sur celle de l'utilisateur.
        utilisateur = getattr(self.context.get('request'), 'user', None)
        compagnie = getattr(utilisateur, 'company', None)
        if compagnie is None:
            compagnie = getattr(self.instance, 'company', None)
        if compagnie is not None and magasin.company_id != compagnie.id:
            raise serializers.ValidationError(
                'Ce magasin ne fait pas partie de votre entreprise.')
        return magasin


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
