"""
Annulation d'une vente encaissee : remboursement automatique (regle validee).

Regle metier retenue, apres decision du commercant :

  « Annuler une vente deja encaissee rembourse ce qui a ete encaisse. »

Concretement, a l'annulation :
  1. un CONTRE-MOUVEMENT est ecrit pour chaque paiement (montant negatif, meme
     methode, meme caisse, reference ANNUL-...) : la trace est complete ;
  2. les especes sont retirees du solde de la caisse concernee ;
  3. la creance du client est diminuee du credit accorde sur cette vente ;
  4. le montant paye de la vente revient a ZERO, statut « Rembourse » ;
  5. le stock des articles est rendu (comportement deja en place).

Garde-fous verrouilles ici :
  - caisse deja fermee (session cloturee) : le solde n'est PAS touche, la
    trace du contre-mouvement le precise ;
  - un retour deja enregistre sur la vente : l'annulation est REFUSEE, sinon
    l'argent serait rendu deux fois ;
  - creance client jamais negative : elle est plafonnee a zero, et tracee ;
  - vente non payee : annulation sans aucun mouvement d'argent.

Lancer :

    py manage.py test tests.test_annulation_remboursement -v 2
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from rest_framework import status

from apps.inventory.models import StockLevel
from apps.partners.models import Partner, PartnerType
from apps.pos.models import CashRegister, RegisterStatus
from apps.sales.models import (Payment, PaymentMethod, PaymentStatus, Sale,
                               SaleStatus)
from apps.sales.services import SaleService
from tests.test_nexora_backend import BaseNexoraTestCase


class AnnulationRemboursementTests(BaseNexoraTestCase):
    """L'annulation rembourse : especes, credit, trace et garde-fous."""

    def setUp(self):
        super().setUp()
        self.client_pro = Partner.objects.create(
            company=self.company_a, name='Boutique Zongo',
            partner_type=PartnerType.CUSTOMER)
        self.caisse = CashRegister.objects.create(
            company=self.company_a, store=self.store_a, name='Caisse A', code='REG-A')
        self.client_a.force_authenticate(user=self.user_a)
        ouverture = self.client_a.post(f'/api/v1/registers/{self.caisse.id}/open_session/',
                                       {'opening_balance': '100.00'})
        self.assertEqual(ouverture.status_code, status.HTTP_201_CREATED, ouverture.content[:200])
        self.caisse.refresh_from_db()

    # ------------------------------------------------------------------ outils

    def _vente(self, montant='70.00', methode=PaymentMethod.CASH, avec_client=False,
               quantite='2.00'):
        """Une vente encaissee, a la caisse ouverte."""
        return SaleService.create_and_complete_sale(
            company=self.company_a, store=self.store_a, seller=self.user_a,
            register=self.caisse,
            customer=self.client_pro if avec_client else None,
            items_data=[{'product': self.product_a2, 'quantity': Decimal(quantite),
                         'unit_price': Decimal('35.00'), 'tax_rate': Decimal('0.00')}],
            payment_data={'amount': Decimal(montant), 'method': methode},
        )

    def _contre_mouvements(self, vente):
        return Payment.objects.filter(sale=vente, amount__lt=Decimal('0.00'))

    # ------------------------------------------------------------------ 1-2-3

    def test_annulation_rembourse_les_especes_et_rend_le_stock(self):
        """Vente 70 F comptant : la caisse revient a 100 F, la vente a 0 F."""
        stock_avant = StockLevel.objects.get(store=self.store_a,
                                             product=self.product_a2).quantity
        vente = self._vente()
        self.caisse.refresh_from_db()
        self.assertEqual(self.caisse.current_balance, Decimal('170.00'))
        self.assertEqual(vente.paid_amount, Decimal('70.00'))

        SaleService.cancel_sale(vente, user=self.user_a, reason='Client a change d avis')
        vente.refresh_from_db()
        self.caisse.refresh_from_db()

        self.assertEqual(vente.status, SaleStatus.CANCELLED)
        self.assertEqual(vente.paid_amount, Decimal('0.00'))
        self.assertEqual(vente.payment_status, PaymentStatus.REFUNDED)
        # 100 F d'ouverture, l'argent de la vente annulee n'y est plus
        self.assertEqual(self.caisse.current_balance, Decimal('100.00'))
        # stock rendu
        stock_apres = StockLevel.objects.get(store=self.store_a,
                                             product=self.product_a2).quantity
        self.assertEqual(stock_apres, stock_avant)

        contre = self._contre_mouvements(vente)
        self.assertEqual(contre.count(), 1)
        self.assertEqual(contre.first().amount, Decimal('-70.00'))
        self.assertEqual(contre.first().payment_method, PaymentMethod.CASH)
        self.assertIn('ANNUL-', contre.first().reference)
        self.assertEqual(contre.first().processed_by, self.user_a)

    def test_annulation_annule_la_creance_du_client(self):
        """Vente a credit 500 F : la creance du client revient a zero."""
        vente = self._vente(montant='500.00', methode=PaymentMethod.CREDIT,
                            avec_client=True, quantite='1.00')
        self.client_pro.refresh_from_db()
        # 35 F de marchandise : on force la vente a 35 F pour rester coherent
        self.assertEqual(vente.total_amount, Decimal('35.00'))

        SaleService.cancel_sale(vente, user=self.user_a, reason='Erreur de saisie')
        vente.refresh_from_db()
        self.client_pro.refresh_from_db()
        self.caisse.refresh_from_db()

        self.assertEqual(vente.paid_amount, Decimal('0.00'))
        self.assertEqual(self.client_pro.current_balance, Decimal('0.00'))
        # un credit n'entre pas en caisse
        self.assertEqual(self.caisse.current_balance, Decimal('100.00'))
        contre = self._contre_mouvements(vente)
        self.assertEqual(contre.count(), 1)
        self.assertEqual(contre.first().payment_method, PaymentMethod.CREDIT)

    def test_annulation_mixte_especes_et_credit(self):
        """300 F comptant + 200 F a credit : chaque partie est reprise."""
        vente = self._vente(montant='300.00', quantite='1.00', avec_client=True)
        self.assertEqual(vente.total_amount, Decimal('35.00'))
        # deuxieme paiement a credit, pour le reste
        SaleService.process_payment(company=self.company_a, sale=vente,
                                    amount=Decimal('200.00'),
                                    method=PaymentMethod.CREDIT,
                                    register=self.caisse, user=self.user_a)
        vente.refresh_from_db()
        self.caisse.refresh_from_db()
        self.client_pro.refresh_from_db()
        self.assertEqual(vente.paid_amount, Decimal('500.00'))
        self.assertEqual(self.caisse.current_balance, Decimal('400.00'))
        self.assertEqual(self.client_pro.current_balance, Decimal('200.00'))

        SaleService.cancel_sale(vente, user=self.user_a, reason='Annulation mixte')
        vente.refresh_from_db()
        self.caisse.refresh_from_db()
        self.client_pro.refresh_from_db()

        self.assertEqual(vente.paid_amount, Decimal('0.00'))
        self.assertEqual(self.caisse.current_balance, Decimal('100.00'))
        self.assertEqual(self.client_pro.current_balance, Decimal('0.00'))
        self.assertEqual(self._contre_mouvements(vente).count(), 2)

    # ------------------------------------------------------------------ garde-fous

    def test_caisse_fermee_le_solde_est_inchange_mais_tout_est_trace(self):
        """Caisse cloturee : on ne touche plus au solde, mais la trace reste."""
        vente = self._vente()
        self.caisse.refresh_from_db()
        self.assertEqual(self.caisse.current_balance, Decimal('170.00'))

        self.client_a.post(f'/api/v1/registers/{self.caisse.id}/close_session/',
                           {'closing_balance': '170.00'})
        self.caisse.refresh_from_db()
        self.assertEqual(self.caisse.status, RegisterStatus.CLOSED)

        SaleService.cancel_sale(vente, user=self.user_a, reason='Apres cloture')
        vente.refresh_from_db()
        self.caisse.refresh_from_db()

        self.assertEqual(vente.paid_amount, Decimal('0.00'))
        self.assertEqual(vente.payment_status, PaymentStatus.REFUNDED)
        # le solde de la caisse cloturee n'est pas modifie...
        self.assertEqual(self.caisse.current_balance, Decimal('170.00'))
        # ... mais le contre-mouvement existe et le dit
        contre = self._contre_mouvements(vente).first()
        self.assertIsNotNone(contre)
        self.assertIn('caisse', contre.reference.lower())

    def test_annulation_refusee_si_un_retour_existe(self):
        """Un retour a deja rendu stock et argent : pas de deuxieme remboursement."""
        vente = self._vente()
        SaleService.process_return(
            sale=vente, user=self.user_a, reason='Un article rendu',
            return_items=[{'product': self.product_a2, 'quantity': Decimal('1.00'),
                           'unit_price': Decimal('35.00')}])
        vente.refresh_from_db()
        paiements_avant = Payment.objects.filter(sale=vente).count()

        with self.assertRaises(ValidationError):
            SaleService.cancel_sale(vente, user=self.user_a, reason='Tentative')

        vente.refresh_from_db()
        self.assertEqual(vente.status, SaleStatus.COMPLETED)
        self.assertEqual(Payment.objects.filter(sale=vente).count(), paiements_avant)

    def test_creance_jamais_negative(self):
        """Si la creance est deja a zero, elle ne devient pas negative."""
        vente = self._vente(montant='300.00', quantite='1.00', avec_client=True)
        SaleService.process_payment(company=self.company_a, sale=vente,
                                    amount=Decimal('200.00'),
                                    method=PaymentMethod.CREDIT,
                                    register=self.caisse, user=self.user_a)
        # la creance a ete « soldee » par ailleurs : on la remet a zero
        self.client_pro.current_balance = Decimal('0.00')
        self.client_pro.save()

        SaleService.cancel_sale(vente, user=self.user_a, reason='Creance soldee')
        self.client_pro.refresh_from_db()
        vente.refresh_from_db()
        self.assertEqual(self.client_pro.current_balance, Decimal('0.00'))
        self.assertEqual(vente.paid_amount, Decimal('0.00'))

    def test_vente_non_payee_annulee_sans_mouvement_d_argent(self):
        """Rien n'a ete encaisse : il n'y a rien a rembourser."""
        vente = SaleService.create_and_complete_sale(
            company=self.company_a, store=self.store_a, seller=self.user_a,
            register=self.caisse,
            items_data=[{'product': self.product_a2, 'quantity': Decimal('1.00'),
                         'unit_price': Decimal('35.00'), 'tax_rate': Decimal('0.00')}],
        )
        self.assertEqual(vente.payment_status, PaymentStatus.PENDING)
        self.caisse.refresh_from_db()

        SaleService.cancel_sale(vente, user=self.user_a, reason='Jamais payee')
        vente.refresh_from_db()
        self.caisse.refresh_from_db()

        self.assertEqual(vente.status, SaleStatus.CANCELLED)
        self.assertEqual(vente.paid_amount, Decimal('0.00'))
        self.assertEqual(vente.payment_status, PaymentStatus.PENDING)
        self.assertEqual(Payment.objects.filter(sale=vente).count(), 0)
        self.assertEqual(self.caisse.current_balance, Decimal('100.00'))

    def test_annulation_par_l_api_rembourse_aussi(self):
        """Le chemin utilise par l'application (POST .../cancel/) rembourse
        de la meme facon : la reponse montre une vente a 0 F, remboursee."""
        vente = self._vente()
        reponse = self.client_a.post(f'/api/v1/sales/{vente.id}/cancel/',
                                     {'reason': 'Annulation depuis l application'},
                                     format='json')
        self.assertEqual(reponse.status_code, status.HTTP_200_OK, reponse.content[:300])
        self.assertEqual(reponse.data['status'], SaleStatus.CANCELLED)
        vente.refresh_from_db()
        self.caisse.refresh_from_db()
        self.assertEqual(reponse.data['paid_amount'], '0.00')
        self.assertEqual(reponse.data['payment_status'], PaymentStatus.REFUNDED)
        self.assertEqual(vente.paid_amount, Decimal('0.00'))
        self.assertEqual(self.caisse.current_balance, Decimal('100.00'))

    def test_annulation_deux_fois_refusee(self):
        """Une vente deja annulee ne peut pas etre annulee de nouveau."""
        vente = self._vente()
        SaleService.cancel_sale(vente, user=self.user_a, reason='Premiere')
        vente.refresh_from_db()
        paiements = Payment.objects.filter(sale=vente).count()

        with self.assertRaises(ValidationError):
            SaleService.cancel_sale(vente, user=self.user_a, reason='Deuxieme')

        self.assertEqual(Payment.objects.filter(sale=vente).count(), paiements)
