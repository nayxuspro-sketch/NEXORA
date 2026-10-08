"""
Les champs de montant doivent etre des Decimal, jamais des flottants.

Un DecimalField dont le defaut est ecrit 0.00 (au lieu de Decimal('0.00'))
rend un flottant pour tout objet neuf qui n'a pas encore ete relu depuis la
base. Le premier calcul d'argent sur cet objet leve alors
TypeError: unsupported operand type(s) for +=: 'float' and 'decimal.Decimal'
et, ailleurs, un arrondi peut fausser un centime en silence.

Ces tests verrouillent :
  1. la regle generale : tout defaut declare sur un champ Decimal doit etre
     un Decimal (inventaire exhaustif de tous les modeles du projet) ;
  2. les deux parcours d'argent reellement concernes : encaisser une vente
     neuve sur une caisse neuve, puis vendre a credit a un client neuf ;
  3. la meme regle cote API : aucun champ de formulaire ne doit declarer un
     defaut flottant, et une vente envoyee sans remise globale reste en
     Decimal de bout en bout.

Lancer :

    py manage.py test tests.test_montants_decimaux -v 2
"""

from decimal import Decimal

import importlib
import inspect

from django.apps import apps
from django.db import models
from django.test import TestCase
from rest_framework import serializers as drf_serializers
from rest_framework import status

from apps.inventory.models import StockLevel
from apps.partners.models import Partner, PartnerType
from apps.pos.models import CashRegister
from apps.sales.models import PaymentMethod, PaymentStatus, Sale
from apps.sales.services import SaleService
from tests.test_nexora_backend import BaseNexoraTestCase


class DefautsDeChampsTests(TestCase):
    """Regle generale : un champ Decimal n'a jamais un defaut flottant."""

    def test_tout_defaut_de_champ_decimal_est_un_decimal(self):
        """Inventaire de tous les modeles : aucun defaut flottant."""
        suspects = []
        champs_decimal = 0
        for config in apps.get_app_configs():
            for modele in config.get_models():
                for champ in modele._meta.get_fields():
                    if not isinstance(champ, models.DecimalField):
                        continue
                    champs_decimal += 1
                    if not champ.has_default():
                        continue          # champ obligatoire : pas de defaut
                    defaut = champ.get_default()
                    if not isinstance(defaut, Decimal):
                        suspects.append(
                            '%s.%s = %r (type %s)' % (
                                modele.__name__, champ.name, defaut,
                                type(defaut).__name__,
                            )
                        )
        self.assertGreater(champs_decimal, 40)
        self.assertEqual(
            suspects, [],
            'Defauts flottants sur des champs Decimal (%d) :\n  %s'
            % (len(suspects), '\n  '.join(suspects)),
        )

    def test_aucun_formulaire_ne_declare_de_defaut_flottant(self):
        """Inventaire de tous les serialiseurs : aucun defaut flottant."""
        suspects = []
        champs_inspectes = 0
        for config in apps.get_app_configs():
            try:
                module = importlib.import_module('%s.serializers' % config.name)
            except ModuleNotFoundError:
                continue
            for nom in dir(module):
                objet = getattr(module, nom)
                if not (inspect.isclass(objet) and issubclass(objet, drf_serializers.Serializer)):
                    continue
                try:
                    champs = objet().fields
                except Exception:
                    continue          # classe de base du framework
                for nom_champ, champ in champs.items():
                    champs_inspectes += 1
                    if isinstance(getattr(champ, 'default', None), float):
                        suspects.append('%s.%s = %r (type float)'
                                        % (objet.__name__, nom_champ, champ.default))
        self.assertGreater(champs_inspectes, 100)
        self.assertEqual(
            suspects, [],
            'Defauts flottants dans des formulaires (%d) :\n  %s'
            % (len(suspects), '\n  '.join(suspects)),
        )


class EncaissementSurObjetsNeufsTests(BaseNexoraTestCase):
    """L'argent reel : vente neuve, caisse neuve, client neuf."""

    def _vente_neuve(self, **extra):
        """Une vente creee en memoire, sans montants passes explicitement."""
        champs = {
            'company': self.company_a,
            'store': self.store_a,
            'reference': 'V-NEUVE-1',
            'total_amount': Decimal('800.00'),
            'subtotal_amount': Decimal('800.00'),
            'tax_amount': Decimal('0.00'),
        }
        champs.update(extra)
        return Sale.objects.create(**champs)

    def test_encaisser_une_vente_neuve_sur_une_caisse_neuve(self):
        """800 F en especes : la vente passe a PAID, la caisse monte a 800 F.

        Le solde de la caisse est additionne a un Decimal : il doit donc
        etre un Decimal des la creation, sans relecture en base.
        """
        caisse = CashRegister.objects.create(
            company=self.company_a, store=self.store_a,
            name='Caisse 01', code='REG-01',
        )
        vente = self._vente_neuve()

        self.assertEqual(vente.paid_amount, Decimal('0.00'))
        self.assertEqual(caisse.current_balance, Decimal('0.00'))

        SaleService.process_payment(
            company=self.company_a, sale=vente, amount=Decimal('800.00'),
            method=PaymentMethod.CASH, register=caisse,
        )

        self.assertEqual(vente.paid_amount, Decimal('800.00'))
        self.assertEqual(vente.payment_status, PaymentStatus.PAID)
        self.assertEqual(caisse.current_balance, Decimal('800.00'))

    def test_vente_sans_remise_globale_reste_en_decimal(self):
        """Une vente envoyee sans remise globale : controlee, acceptee, et
        enregistree en Decimal, avec le stock decremente."""
        reponse = self.client_a.post('/api/v1/sales/', {
            'store': str(self.store_a.id),
            'items': [{
                'product': str(self.product_a1.id), 'quantity': 1,
                'unit_price': '800.00', 'tax_rate': '20.00',
            }],
        }, format='json')
        self.assertEqual(reponse.status_code, status.HTTP_201_CREATED, reponse.content[:300])

        vente = Sale.objects.get(id=reponse.data['id'])
        self.assertEqual(vente.discount_amount, Decimal('0.00'))
        self.assertEqual(vente.subtotal_amount, Decimal('800.00'))
        self.assertEqual(vente.tax_amount, Decimal('160.00'))
        self.assertEqual(vente.total_amount, Decimal('960.00'))
        stock = StockLevel.objects.get(store=self.store_a, product=self.product_a1)
        self.assertEqual(stock.quantity, Decimal('49.00'))   # 50 en stock, 1 vendu

    def test_vendre_a_credit_a_un_client_neuf(self):
        """Vente a credit de 500 F : la creance du client monte a 500 F."""
        client = Partner.objects.create(
            company=self.company_a, name='Client Comptoir',
            partner_type=PartnerType.CUSTOMER,
        )
        vente = self._vente_neuve(
            reference='V-NEUVE-2', customer=client,
            total_amount=Decimal('500.00'), subtotal_amount=Decimal('500.00'),
        )

        self.assertEqual(client.current_balance, Decimal('0.00'))

        SaleService.process_payment(
            company=self.company_a, sale=vente, amount=Decimal('500.00'),
            method=PaymentMethod.CREDIT,
        )

        self.assertEqual(client.current_balance, Decimal('500.00'))
        self.assertEqual(vente.paid_amount, Decimal('500.00'))
        self.assertEqual(vente.payment_status, PaymentStatus.PAID)
