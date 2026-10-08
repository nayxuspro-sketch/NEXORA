"""
Les regles d'argent : montants, TVA, remises, paiements, retours, cloture.

Ces tests verrouillent les calculs qui touchent l'argent, pour qu'une
modification future ne puisse pas les fausser en silence. Ils completent les
tests de stock (deja presents) et les 14 tests du bilan vendeur.

Conventions de la maison (verifiees dans le code) :
  - montant HT d'une ligne   = quantite x prix unitaire
  - remise de ligne          = HT de la ligne x taux de remise
  - TVA                      = (HT de ligne - remise de ligne) x taux de TVA
  - total de ligne           = HT - remise + TVA
  - sous-total de la vente   = somme des lignes (HT - remise)
  - total de la vente        = (sous-total + TVA) - remise globale, jamais negatif
  - paiement                 = solde, jamais negatif ; PAID si >= total sinon PARTIAL
  - retour                   = quantite x prix paye lors de la vente
  - cloture de caisse        = ecart entre l'espece comptee et le solde attendu

Lancer :

    py manage.py test tests.test_regles_argent -v 2
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from rest_framework import status

from apps.catalog.models import Product
from apps.inventory.models import StockLevel
from apps.pos.models import CashRegister, RegisterSession, RegisterStatus
from apps.sales.models import Payment, PaymentMethod, PaymentStatus, Sale, SaleReturn, SaleStatus
from apps.sales.services import SaleService
from tests.test_nexora_backend import BaseNexoraTestCase


class MontantsVenteTests(BaseNexoraTestCase):
    """Calcul des montants : ligne, TVA, remises, total."""

    def test_montants_de_ligne_avec_remise(self):
        """2 x 800 F, remise de ligne 10 %, TVA 20 % : HT 1600, remise 160,
        TVA 288, total de ligne 1728."""
        reponse = self.client_a.post('/api/v1/sales/', {
            'store': str(self.store_a.id),
            'items': [{
                'product': str(self.product_a1.id), 'quantity': 2,
                'unit_price': '800.00', 'tax_rate': '20.00', 'discount_rate': '10.00',
            }],
        }, format='json')
        self.assertEqual(reponse.status_code, status.HTTP_201_CREATED, reponse.content[:300])

        vente = Sale.objects.get(id=reponse.data['id'])
        self.assertEqual(vente.subtotal_amount, Decimal('1440.00'))   # 1600 - 160
        self.assertEqual(vente.tax_amount, Decimal('288.00'))          # 1440 x 20 %
        self.assertEqual(vente.total_amount, Decimal('1728.00'))       # 1440 + 288
        ligne = vente.items.get()
        self.assertEqual(ligne.total, Decimal('1728.00'))

    def test_remise_globale_apres_taxe(self):
        """La remise globale se deduit du TTC : 1728 - 100 = 1628."""
        reponse = self.client_a.post('/api/v1/sales/', {
            'store': str(self.store_a.id),
            'discount_amount': '100.00',
            'items': [{
                'product': str(self.product_a1.id), 'quantity': 2,
                'unit_price': '800.00', 'tax_rate': '20.00', 'discount_rate': '10.00',
            }],
        }, format='json')
        vente = Sale.objects.get(id=reponse.data['id'])
        self.assertEqual(vente.total_amount, Decimal('1628.00'))
        self.assertEqual(vente.subtotal_amount, Decimal('1440.00'))
        self.assertEqual(vente.tax_amount, Decimal('288.00'))

    def test_total_jamais_negatif(self):
        """Une remise globale superieure au TTC ramene le total a 0, jamais negatif."""
        reponse = self.client_a.post('/api/v1/sales/', {
            'store': str(self.store_a.id),
            'discount_amount': '9999.00',
            'items': [{'product': str(self.product_a1.id), 'quantity': 1,
                       'unit_price': '100.00', 'tax_rate': '20.00'}],
        }, format='json')
        vente = Sale.objects.get(id=reponse.data['id'])
        self.assertEqual(vente.total_amount, Decimal('0.00'))

    def test_sans_paiement_la_vente_reste_a_payer(self):
        """Vente sans reglement : PENDING, rien d'encaisse."""
        reponse = self.client_a.post('/api/v1/sales/', {
            'store': str(self.store_a.id),
            'items': [{'product': str(self.product_a1.id), 'quantity': 1}],
        }, format='json')
        vente = Sale.objects.get(id=reponse.data['id'])
        self.assertEqual(vente.payment_status, PaymentStatus.PENDING)
        self.assertEqual(vente.paid_amount, Decimal('0.00'))


class PaiementsTests(BaseNexoraTestCase):
    """Encaissements : statuts, caisse, credit client."""

    def setUp(self):
        super().setUp()
        self.caisse = CashRegister.objects.create(
            company=self.company_a, store=self.store_a, name='Caisse 1', code='C1')
        # La caisse est relue depuis la base, comme le fait le vrai POS : le
        # defaut du modele (0.00, un flottant) provoque sinon un TypeError au
        # premier encaissement. Voir la notice : point signale, non modifie.
        self.caisse.refresh_from_db()
        # Le client est relu depuis la base : son defaut de modele est aussi un
        # flottant (0.00), et le service y ajoute un Decimal (meme point signale
        # que la caisse).
        self.customer_a.refresh_from_db()
        self.vente = SaleService.create_and_complete_sale(
            company=self.company_a, store=self.store_a, seller=self.user_a, customer=self.customer_a,
            items_data=[{'product': self.product_a1, 'quantity': Decimal('2.00'),
                         'unit_price': Decimal('800.00'), 'tax_rate': Decimal('20.00')}],
        )

    def test_paiement_complet_en_especes(self):
        """Paiement total en especes : PAID, solde exact, caisse creditee."""
        self.assertEqual(self.vente.total_amount, Decimal('1920.00'))
        SaleService.process_payment(
            company=self.company_a, sale=self.vente, amount=Decimal('1920.00'),
            method=PaymentMethod.CASH, register=self.caisse, user=self.user_a)
        self.vente.refresh_from_db()
        self.caisse.refresh_from_db()
        self.assertEqual(self.vente.payment_status, PaymentStatus.PAID)
        self.assertEqual(self.vente.paid_amount, Decimal('1920.00'))
        self.assertEqual(self.caisse.current_balance, Decimal('1920.00'))

    def test_paiement_partiel_puis_solde(self):
        """500 F sur 1920 F : PARTIAL ; puis le solde : PAID."""
        SaleService.process_payment(company=self.company_a, sale=self.vente, amount=Decimal('500.00'),
                                    method=PaymentMethod.CASH, user=self.user_a)
        self.vente.refresh_from_db()
        self.assertEqual(self.vente.payment_status, PaymentStatus.PARTIAL)
        self.assertEqual(self.vente.paid_amount, Decimal('500.00'))

        SaleService.process_payment(company=self.company_a, sale=self.vente, amount=Decimal('1420.00'),
                                    method=PaymentMethod.CASH, user=self.user_a)
        self.vente.refresh_from_db()
        self.assertEqual(self.vente.payment_status, PaymentStatus.PAID)
        self.assertEqual(self.vente.paid_amount, Decimal('1920.00'))

    def test_paiement_nul_ou_negatif_refuse(self):
        """On n'encaisse ni 0 ni un montant negatif."""
        for montant in (Decimal('0.00'), Decimal('-10.00')):
            with self.assertRaises(ValidationError):
                SaleService.process_payment(company=self.company_a, sale=self.vente, amount=montant,
                                            method=PaymentMethod.CASH, user=self.user_a)

    def test_paiement_credit_ne_touche_pas_la_caisse(self):
        """Reglement a credit : la creance du client augmente, la caisse reste intacte."""
        self.assertEqual(self.customer_a.current_balance, Decimal('0.00'))
        SaleService.process_payment(company=self.company_a, sale=self.vente, amount=Decimal('1920.00'),
                                    method=PaymentMethod.CREDIT, register=self.caisse, user=self.user_a)
        self.customer_a.refresh_from_db()
        self.caisse.refresh_from_db()
        self.assertEqual(self.customer_a.current_balance, Decimal('1920.00'))
        self.assertEqual(self.caisse.current_balance, Decimal('0.00'))

    def test_trop_percu_est_accepte_et_trace(self):
        """Un client qui donne plus (2000 pour 1920) : PAID et le trop-percu est visible."""
        SaleService.process_payment(company=self.company_a, sale=self.vente, amount=Decimal('2000.00'),
                                    method=PaymentMethod.CASH, register=self.caisse, user=self.user_a)
        self.vente.refresh_from_db()
        self.assertEqual(self.vente.payment_status, PaymentStatus.PAID)
        self.assertEqual(self.vente.paid_amount, Decimal('2000.00'))


class RetoursTests(BaseNexoraTestCase):
    """Retours : montant rembourse, refus des cas incoherents."""

    def _vente(self, quantite='2.00', prix='800.00'):
        reponse = self.client_a.post('/api/v1/sales/', {
            'store': str(self.store_a.id), 'customer': str(self.customer_a.id),
            'items': [{'product': str(self.product_a1.id), 'quantity': Decimal(quantite),
                       'unit_price': prix, 'tax_rate': '20.00'}],
        }, format='json')
        self.assertEqual(reponse.status_code, status.HTTP_201_CREATED, reponse.content[:300])
        return Sale.objects.get(id=reponse.data['id'])

    def _retour(self, vente, quantite='1.00', produit=None, **extra):
        charge = {'reason': 'Unite defectueuse',
                  'items': [{'product': str((produit or self.product_a1).id), 'quantity': Decimal(quantite)}]}
        charge.update(extra)
        return self.client_a.post(f'/api/v1/sales/{vente.id}/return_items/', charge, format='json')

    def test_remboursement_au_prix_de_la_vente(self):
        """Le remboursement se calcule au prix PAYE, pas au tarif du jour.

        Vente de 2 articles a 800 F, puis le tarif passe a 900 F : rendre
        1 article doit rembourser 800 F, jamais 900 F.
        """
        vente = self._vente(quantite='2.00', prix='800.00')
        Product.objects.filter(id=self.product_a1.id).update(selling_price=Decimal('900.00'))

        reponse = self._retour(vente, quantite='1.00')
        self.assertEqual(reponse.status_code, status.HTTP_201_CREATED, reponse.content[:300])
        retour = SaleReturn.objects.get(sale=vente)
        self.assertEqual(retour.refund_amount, Decimal('800.00'))

    def test_remboursement_partiel_et_stock_rendu(self):
        """Rendre 2 articles sur 2 : 1600 F rembourses et stock restaure."""
        vente = self._vente(quantite='2.00', prix='800.00')
        stock_avant = StockLevel.objects.get(store=self.store_a, product=self.product_a1).quantity

        reponse = self._retour(vente, quantite='2.00')
        self.assertEqual(reponse.status_code, status.HTTP_201_CREATED, reponse.content[:300])
        retour = SaleReturn.objects.get(sale=vente)
        self.assertEqual(retour.refund_amount, Decimal('1600.00'))
        stock_apres = StockLevel.objects.get(store=self.store_a, product=self.product_a1).quantity
        self.assertEqual(stock_apres, stock_avant + Decimal('2.00'))

    def test_retour_superieur_a_la_quantite_vendue_refuse(self):
        """Rendre 3 articles quand 2 ont ete vendus : refus."""
        vente = self._vente(quantite='2.00')
        reponse = self._retour(vente, quantite='3.00')
        self.assertEqual(reponse.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(SaleReturn.objects.filter(sale=vente).exists())

    def test_retour_d_un_article_non_vendu_refuse(self):
        """Rendre un article qui n'etait pas dans la vente : refus."""
        vente = self._vente(quantite='2.00')
        reponse = self._retour(vente, quantite='1.00', produit=self.product_a2)
        self.assertEqual(reponse.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retour_sur_vente_annulee_refuse(self):
        """Une vente annulee ne peut plus faire l'objet d'un retour."""
        vente = self._vente(quantite='2.00')
        SaleService.cancel_sale(vente, user=self.user_a, reason='Erreur de saisie')
        reponse = self._retour(vente, quantite='1.00')
        self.assertEqual(reponse.status_code, status.HTTP_400_BAD_REQUEST)


class ClotureCaisseTests(BaseNexoraTestCase):
    """Cloture : solde attendu et ecart d'espece."""

    def test_cloture_calcule_l_ecart_d_espece(self):
        """Ouverture 100 F, vente especes 70 F, comptage 165 F : ecart -5 F."""
        caisse = CashRegister.objects.create(
            company=self.company_a, store=self.store_a, name='Caisse Z', code='CZ')
        caisse.refresh_from_db()

        ouverture = self.client_a.post(f'/api/v1/registers/{caisse.id}/open_session/',
                                       {'opening_balance': '100.00'})
        self.assertEqual(ouverture.status_code, status.HTTP_201_CREATED, ouverture.content[:300])
        # L'ouverture a ete faite par l'API, sur une autre instance : il faut
        # relire la caisse, sinon l'encaissement ecrirait sur un objet perime.
        caisse.refresh_from_db()
        self.assertEqual(caisse.current_balance, Decimal('100.00'))

        SaleService.create_and_complete_sale(
            company=self.company_a, store=self.store_a, seller=self.user_a, register=caisse,
            items_data=[{'product': self.product_a2, 'quantity': Decimal('2.00'),
                         'unit_price': Decimal('35.00'), 'tax_rate': Decimal('0.00')}],
            payment_data={'amount': Decimal('70.00'), 'method': PaymentMethod.CASH},
        )
        caisse.refresh_from_db()
        self.assertEqual(caisse.current_balance, Decimal('170.00'))

        fermeture = self.client_a.post(f'/api/v1/registers/{caisse.id}/close_session/',
                                       {'closing_balance': '165.00'})
        self.assertEqual(fermeture.status_code, status.HTTP_200_OK, fermeture.content[:300])

        session = RegisterSession.objects.filter(register=caisse).order_by('-opened_at').first()
        self.assertTrue(session.is_closed)
        self.assertEqual(session.closing_balance, Decimal('165.00'))
        self.assertEqual(session.difference, Decimal('-5.00'))
        caisse.refresh_from_db()
        self.assertEqual(caisse.status, RegisterStatus.CLOSED)


class AnnulationEtPaiementTests(BaseNexoraTestCase):
    """Annulation d'une vente deja encaissee : remboursement (regle du 8/10/2026).

    Regle validee par le commercant : annuler une vente deja encaissee rembourse
    ce qui a ete encaisse (contre-mouvement par paiement, caisse debitee des
    especes, creance client diminuee, montant paye remis a zero, statut
    « Rembourse »).

    Ce test verifie le cas nominal ici. Les cas complets (credit, paiement
    mixte, caisse deja cloturee, refus si un retour existe, creance plafonnee)
    sont dans tests/test_annulation_remboursement.py.

    Historique : jusqu'au 8 octobre 2026, l'annulation ne touchait pas a
    l'argent — le test de l'epoque le constatait. Il a ete remplace par celui
    de la nouvelle regle, comme il l'annoncait.
    """

    def test_annulation_rembourse_le_paiement(self):
        """Vente 70 F comptant : apres annulation, la caisse revient a 0 et la
        vente affiche 0 F paye, statut « Rembourse »."""
        caisse = CashRegister.objects.create(
            company=self.company_a, store=self.store_a, name='Caisse Annul', code='CA')
        # Une caisse de boutique est ouverte avant d'encaisser.
        ouverture = self.client_a.post(f'/api/v1/registers/{caisse.id}/open_session/',
                                       {'opening_balance': '0.00'})
        self.assertEqual(ouverture.status_code, 201, ouverture.content[:200])
        caisse.refresh_from_db()
        vente = SaleService.create_and_complete_sale(
            company=self.company_a, store=self.store_a, seller=self.user_a, register=caisse,
            items_data=[{'product': self.product_a2, 'quantity': Decimal('2.00'),
                         'unit_price': Decimal('35.00'), 'tax_rate': Decimal('0.00')}],
            payment_data={'amount': Decimal('70.00'), 'method': PaymentMethod.CASH},
        )
        caisse.refresh_from_db()
        self.assertEqual(caisse.current_balance, Decimal('70.00'))

        SaleService.cancel_sale(vente, user=self.user_a, reason='Client a change d avis')
        vente.refresh_from_db()
        caisse.refresh_from_db()

        self.assertEqual(vente.status, SaleStatus.CANCELLED)
        # Remboursement : le montant paye revient a zero, les especes quittent
        # le solde de la caisse, et le contre-mouvement est trace.
        self.assertEqual(vente.paid_amount, Decimal('0.00'))
        self.assertEqual(vente.payment_status, PaymentStatus.REFUNDED)
        self.assertEqual(caisse.current_balance, Decimal('0.00'))
        contre = Payment.objects.filter(sale=vente, amount__lt=Decimal('0.00')).first()
        self.assertIsNotNone(contre, 'contre-mouvement manquant')
        self.assertEqual(contre.amount, Decimal('-70.00'))
