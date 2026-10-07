# -*- coding: utf-8 -*-
"""
TEST du « Bilan de vente par vendeur » du POS — fichier AUTONOME.

Aucune dépendance à vos autres tests : ce fichier crée lui-même ses données
(entreprise, vendeurs, magasin, produits, ventes) puis appelle le vrai endpoint
/api/v1/sales/export-seller-pdf/ et vérifie le comportement réel.

Exécution (à la racine du projet, dossier de manage.py) :

    py manage.py test tests.test_bilan_vendeur_pos -v 2

Résultat attendu : OK (14 tests).

Ce qui est vérifié :
  1. le bilan ne contient QUE les ventes du vendeur choisi ;
  2. les brouillons et les ventes annulées sont exclus ;
  3. un vendeur inconnu => 404 explicite, jamais le bilan d'un autre ;
  4. un vendeur d'une AUTRE entreprise n'est jamais utilisé ;
  5. un compte CASHIER n'obtient que son propre bilan ;
  6. l'export PDF répond bien et nomme le fichier d'après le vendeur choisi.
"""

import json
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole
from apps.catalog.models import Category, Product, Unit
from apps.companies.models import Company
from apps.inventory.models import Store
from apps.sales.models import Sale, SaleItem, SaleStatus

# Les helpers du correctif portent des noms préfixés (_nexora_*) pour ne pas
# entrer en conflit avec un autre correctif ; on accepte aussi les anciens noms.
try:
    from apps.sales.pdf_seller_report import (
        _nexora_resolve_seller as resolve_seller,
        _nexora_ventes_du_vendeur as sales_queryset_for_seller,
    )
except ImportError:  # ancienne version du correctif
    from apps.sales.pdf_seller_report import resolve_seller, sales_queryset_for_seller

URL_EXPORT = '/api/v1/sales/export-seller-pdf/'


class BilanVendeurPosTests(TestCase):
    """Bilan de vente par vendeur : endpoint export-seller-pdf du POS."""

    @classmethod
    def setUpTestData(cls):
        cls.company = Company.objects.create(name='Nexora Test', slug='nexora-test')

    def setUp(self):
        self.company = self.__class__.company

        self.administrateur = User.objects.create_user(
            email='admin.test@nexora.local', password='Password123!',
            first_name='Admin', last_name='Test',
            company=self.company, role=UserRole.ADMIN)
        self.vendeur1 = User.objects.create_user(
            email='awa.traore@nexora.local', password='Password123!',
            first_name='Awa', last_name='Traore',
            company=self.company, role=UserRole.CASHIER)
        self.vendeur2 = User.objects.create_user(
            email='boubacar.kone@nexora.local', password='Password123!',
            first_name='Boubacar', last_name='Kone',
            company=self.company, role=UserRole.CASHIER)

        self.autre_entreprise = Company.objects.create(name='Beta Test', slug='beta-test')
        self.utilisateur_beta = User.objects.create_user(
            email='chef@beta.local', password='Password123!',
            first_name='Chef', last_name='Beta',
            company=self.autre_entreprise, role=UserRole.ADMIN)

        self.magasin = Store.objects.create(company=self.company, name='Magasin Test', code='MAG-T')
        self.magasin_beta = Store.objects.create(
            company=self.autre_entreprise, name='Magasin Beta', code='MAG-B')

        self.categorie = Category.objects.create(company=self.company, name='Divers', slug='divers')
        self.unite = Unit.objects.create(company=self.company, name='Piece', symbol='pcs')
        self.produit = Product.objects.create(
            company=self.company, name='Article Test', sku='ART-TEST-01',
            category=self.categorie, unit=self.unite,
            cost_price=Decimal('100.00'), selling_price=Decimal('1000.00'))
        self.produit_beta = Product.objects.create(
            company=self.autre_entreprise, name='Article Beta', sku='ART-BETA-01',
            cost_price=Decimal('100.00'), selling_price=Decimal('1000.00'))

        self.client_admin = APIClient()
        self.client_admin.force_authenticate(user=self.administrateur)
        self.client_vendeur1 = APIClient()
        self.client_vendeur1.force_authenticate(user=self.vendeur1)

        aujourdhui = timezone.localdate()

        # Ventes du vendeur 1 : 1 000 + 2 000 = 3 000
        self.vente1 = self._creer_vente('TEST-V1-001', self.vendeur1, Decimal('1000.00'))
        self.vente2 = self._creer_vente('TEST-V1-002', self.vendeur1, Decimal('2000.00'))
        # Vente du vendeur 2 : 4 000
        self.vente3 = self._creer_vente('TEST-V2-001', self.vendeur2, Decimal('4000.00'))

        # Cas exclus du bilan
        self.vente_annulee = self._creer_vente(
            'TEST-V1-ANNULEE', self.vendeur1, Decimal('9999.00'), statut=SaleStatus.CANCELLED)
        self.vente_brouillon = self._creer_vente(
            'TEST-V1-BROUILLON', self.vendeur1, Decimal('8888.00'), statut=SaleStatus.DRAFT)
        self.vente_sans_vendeur = self._creer_vente('TEST-SANS-VENDEUR', None, Decimal('7777.00'))
        self.vente_hors_periode = self._creer_vente(
            'TEST-V1-VIEILLE', self.vendeur1, Decimal('6666.00'), jours_en_arriere=90)
        self.vente_autre_entreprise = self._creer_vente(
            'TEST-BETA-001', self.utilisateur_beta, Decimal('5555.00'),
            entreprise=self.autre_entreprise, magasin=self.magasin_beta,
            produit=self.produit_beta)

        self.debut = (aujourdhui - timezone.timedelta(days=30)).isoformat()
        self.fin = aujourdhui.isoformat()
        self.fenetre_debut = timezone.now() - timezone.timedelta(days=30)
        self.fenetre_fin = timezone.now() + timezone.timedelta(hours=4)

    # ------------------------------------------------------------- outils --

    def _creer_vente(self, reference, vendeur, montant, statut=SaleStatus.COMPLETED,
                      jours_en_arriere=0, entreprise=None, magasin=None, produit=None):
        entreprise = entreprise or self.company
        magasin = magasin or self.magasin
        produit = produit or self.produit
        vente = Sale.objects.create(
            company=entreprise, reference=reference, store=magasin, seller=vendeur,
            status=statut, subtotal_amount=montant, total_amount=montant,
            paid_amount=montant if statut == SaleStatus.COMPLETED else Decimal('0.00'))
        SaleItem.objects.create(
            company=entreprise, sale=vente, product=produit,
            quantity=Decimal('1.00'), unit_price=montant,
            tax_rate=Decimal('0.00'), total=montant)
        if jours_en_arriere:
            date = timezone.now() - timezone.timedelta(days=jours_en_arriere)
            Sale.objects.filter(pk=vente.pk).update(created_at=date)
            vente.refresh_from_db()
        return vente

    def _nom_fichier(self, reponse):
        return reponse.get('Content-Disposition', '')

    # ------------------------------------------------- 1. filtre vendeur --

    def test_queryset_limite_au_vendeur_et_a_la_periode(self):
        qs = sales_queryset_for_seller(
            self.company, self.vendeur1, self.fenetre_debut, self.fenetre_fin)
        references = sorted(qs.values_list('reference', flat=True))
        self.assertEqual(references, ['TEST-V1-001', 'TEST-V1-002'])
        total = sum((v.total_amount for v in qs), Decimal('0.00'))
        self.assertEqual(total, Decimal('3000.00'))

    def test_ventes_annulees_brouillons_et_hors_periode_exclus(self):
        qs = sales_queryset_for_seller(
            self.company, self.vendeur1, self.fenetre_debut, self.fenetre_fin)
        references = set(qs.values_list('reference', flat=True))
        for exclue in ('TEST-V1-ANNULEE', 'TEST-V1-BROUILLON', 'TEST-V1-VIEILLE',
                       'TEST-SANS-VENDEUR'):
            self.assertNotIn(exclue, references)

    def test_le_vendeur2_ne_voit_que_ses_ventes(self):
        qs = sales_queryset_for_seller(
            self.company, self.vendeur2, self.fenetre_debut, self.fenetre_fin)
        self.assertEqual(sorted(qs.values_list('reference', flat=True)), ['TEST-V2-001'])

    def test_cloisonnement_entre_entreprises(self):
        qs = sales_queryset_for_seller(
            self.company, self.vendeur2, self.fenetre_debut, self.fenetre_fin)
        self.assertNotIn('TEST-BETA-001', set(qs.values_list('reference', flat=True)))

    # ------------------------------------------------ 2. resolve_seller --

    def test_resolve_seller_identifie_le_bon_compte(self):
        for cible in (str(self.vendeur1.id), 'awa.traore@nexora.local',
                      'AWA.TRAORE@NEXORA.LOCAL', 'awa.traore', 'Awa Traore'):
            vendeur, erreur = resolve_seller(self.company, cible)
            self.assertIsNone(erreur, 'Cible %s : aucune erreur attendue' % cible)
            self.assertEqual(vendeur, self.vendeur1, 'Cible %s' % cible)

    def test_resolve_seller_refuse_un_vendeur_inconnu(self):
        vendeur, erreur = resolve_seller(self.company, 'personne.inconnue@nexora.local')
        self.assertIsNone(vendeur)
        self.assertIsNotNone(erreur)

    def test_resolve_seller_refuse_un_email_partiel_ambigu(self):
        User.objects.create_user(
            email='awa.traore2@nexora.local', password='Password123!',
            first_name='Awa', last_name='Traore Bis',
            company=self.company, role=UserRole.CASHIER)
        vendeur, erreur = resolve_seller(self.company, 'awa.traore')
        self.assertIsNone(vendeur)
        self.assertIsNotNone(erreur)

    def test_resolve_seller_refuse_un_vendeur_d_une_autre_entreprise(self):
        for cible in (str(self.utilisateur_beta.id), 'chef@beta.local'):
            vendeur, erreur = resolve_seller(self.company, cible)
            self.assertIsNone(vendeur, 'Cible %s' % cible)
            self.assertIsNotNone(erreur, 'Cible %s' % cible)

    # ------------------------------------------------- 3. export PDF ----

    def test_export_pdf_du_vendeur_choisi(self):
        reponse = self.client_vendeur1.get(
            URL_EXPORT, {'start_date': self.debut, 'end_date': self.fin,
                         'seller_id': str(self.vendeur1.id)})
        self.assertEqual(reponse.status_code, 200)
        self.assertIn('application/pdf', reponse['Content-Type'])
        nom = self._nom_fichier(reponse)
        self.assertIn('Awa_Traore', nom)
        self.assertNotIn('Boubacar', nom)

    def test_export_pdf_vendeur2_ne_contient_pas_le_vendeur1(self):
        reponse = self.client_admin.get(
            URL_EXPORT, {'start_date': self.debut, 'end_date': self.fin,
                         'seller_id': str(self.vendeur2.id)})
        self.assertEqual(reponse.status_code, 200)
        nom = self._nom_fichier(reponse)
        self.assertIn('Boubacar_Kone', nom)
        self.assertNotIn('Awa', nom)

    def test_export_pdf_vendeur_inconnu_renvoie_404(self):
        reponse = self.client_admin.get(
            URL_EXPORT, {'start_date': self.debut, 'end_date': self.fin,
                         'seller_id': '00000000-0000-0000-0000-000000000000'})
        self.assertEqual(reponse.status_code, 404)
        self.assertIn('detail', json.loads(reponse.content.decode('utf-8')))

        reponse = self.client_admin.get(
            URL_EXPORT, {'start_date': self.debut, 'end_date': self.fin,
                         'seller': 'inconnu@nexora.local'})
        self.assertEqual(reponse.status_code, 404)

    def test_export_pdf_avec_email_exact(self):
        reponse = self.client_admin.get(
            URL_EXPORT, {'start_date': self.debut, 'end_date': self.fin,
                         'seller': 'boubacar.kone@nexora.local'})
        self.assertEqual(reponse.status_code, 200)
        self.assertIn('Boubacar_Kone', self._nom_fichier(reponse))

    def test_caissier_limite_a_son_propre_bilan(self):
        """Un caissier qui demande le bilan d'un collègue obtient le sien."""
        reponse = self.client_vendeur1.get(
            URL_EXPORT, {'start_date': self.debut, 'end_date': self.fin,
                         'seller_id': str(self.vendeur2.id)})
        self.assertEqual(reponse.status_code, 200)
        nom = self._nom_fichier(reponse)
        self.assertIn('Awa_Traore', nom)
        self.assertNotIn('Boubacar', nom)

    def test_export_sans_parametre_repond_toujours(self):
        reponse = self.client_admin.get(URL_EXPORT, {'start_date': self.debut, 'end_date': self.fin})
        self.assertEqual(reponse.status_code, 200)
        self.assertIn('application/pdf', reponse['Content-Type'])
