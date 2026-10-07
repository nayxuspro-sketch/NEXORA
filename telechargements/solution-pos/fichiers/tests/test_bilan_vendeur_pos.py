# -*- coding: utf-8 -*-
"""
Test Django des correctifs du « Bilan de vente par vendeur » du POS.

Exécution (à la racine du projet, là où se trouve manage.py) :

    py manage.py test tests.test_bilan_vendeur_pos -v 2

Ces tests vérifient, sur la vraie base de test Django :

 1. le bilan est STRICTEMENT limité au vendeur demandé (aucune addition des
    ventes des autres vendeurs) ;
 2. seules les ventes VALIDÉES (COMPLETED) sont comptabilisées : les brouillons
    et les ventes annulées sont exclus ;
 3. un vendeur demandé mais introuvable produit une erreur 404 explicite au lieu
    du bilan d'un autre vendeur ;
 4. un vendeur d'une AUTRE entreprise n'est jamais utilisé ;
 5. un compte de rôle CASHIER n'obtient que son propre bilan ;
 6. l'export PDF répond bien pour le vendeur choisi (nom du vendeur dans le nom
    du fichier produit).
"""

from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole
from apps.sales.models import Sale, SaleItem, SaleStatus
# Les helpers du correctif sont préfixés (_nexora_*) pour ne pas entrer en
# collision avec d'autres correctifs ; on accepte aussi les anciens noms.
try:
    from apps.sales.pdf_seller_report import (
        _nexora_resolve_seller as resolve_seller,
        _nexora_ventes_du_vendeur as sales_queryset_for_seller,
    )
except ImportError:
    from apps.sales.pdf_seller_report import resolve_seller, sales_queryset_for_seller
from tests.test_nexora_backend import BaseNexoraTestCase

URL_EXPORT = '/api/v1/sales/export-seller-pdf/'


class BilanVendeurPosTests(BaseNexoraTestCase):
    """Bilan de vente par vendeur du POS (endpoint export-seller-pdf)."""

    def setUp(self):
        super().setUp()

        # Deux vendeurs de l'entreprise A
        self.vendeur1 = User.objects.create_user(
            email='awa.traore@alpha.com',
            password='Password123!',
            first_name='Awa',
            last_name='Traore',
            company=self.company_a,
            role=UserRole.CASHIER,
        )
        self.vendeur2 = User.objects.create_user(
            email='boubacar.kone@alpha.com',
            password='Password123!',
            first_name='Boubacar',
            last_name='Kone',
            company=self.company_a,
            role=UserRole.CASHIER,
        )

        self.client_vendeur1 = APIClient()
        self.client_vendeur1.force_authenticate(user=self.vendeur1)

        aujourdhui = timezone.localdate()

        # Ventes du vendeur 1 : 1 000 + 2 000 = 3 000
        self.vente1 = self._creer_vente('POS-V1-001', self.vendeur1, Decimal('1000.00'))
        self.vente2 = self._creer_vente('POS-V1-002', self.vendeur1, Decimal('2000.00'))
        # Vente du vendeur 2 : 4 000
        self.vente3 = self._creer_vente('POS-V2-001', self.vendeur2, Decimal('4000.00'))

        # Cas exclus du bilan
        self.vente_annulee = self._creer_vente(
            'POS-V1-ANNULEE', self.vendeur1, Decimal('9999.00'), statut=SaleStatus.CANCELLED
        )
        self.vente_brouillon = self._creer_vente(
            'POS-V1-BROUILLON', self.vendeur1, Decimal('8888.00'), statut=SaleStatus.DRAFT
        )
        self.vente_sans_vendeur = self._creer_vente('POS-SANS-VENDEUR', None, Decimal('7777.00'))
        self.vente_hors_periode = self._creer_vente(
            'POS-V1-VIEILLE', self.vendeur1, Decimal('6666.00'), jours_en_arriere=90
        )
        self.vente_autre_entreprise = self._creer_vente(
            'POS-V2-AUTRE', self.user_b, Decimal('5555.00'),
            entreprise=self.company_b, magasin=self.store_b
        )

        self.debut = (aujourdhui - timezone.timedelta(days=30)).isoformat()
        self.fin = aujourdhui.isoformat()
        self.fenetre_debut = timezone.now() - timezone.timedelta(days=30)
        self.fenetre_fin = timezone.now() + timezone.timedelta(hours=4)

    # ------------------------------------------------------------- outils --

    def _creer_vente(self, reference, vendeur, montant, statut=SaleStatus.COMPLETED,
                      jours_en_arriere=0, entreprise=None, magasin=None):
        entreprise = entreprise or self.company_a
        magasin = magasin or self.store_a
        vente = Sale.objects.create(
            company=entreprise,
            reference=reference,
            store=magasin,
            seller=vendeur,
            status=statut,
            subtotal_amount=montant,
            total_amount=montant,
            paid_amount=montant if statut == SaleStatus.COMPLETED else Decimal('0.00'),
        )
        SaleItem.objects.create(
            company=entreprise,
            sale=vente,
            product=self.product_a1 if entreprise == self.company_a else self.product_b1,
            quantity=Decimal('1.00'),
            unit_price=montant,
            tax_rate=Decimal('0.00'),
            total=montant,
        )
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
            self.company_a, self.vendeur1, self.fenetre_debut, self.fenetre_fin
        )
        references = sorted(qs.values_list('reference', flat=True))
        self.assertEqual(references, ['POS-V1-001', 'POS-V1-002'])

        total = sum((v.total_amount for v in qs), Decimal('0.00'))
        self.assertEqual(total, Decimal('3000.00'))

    def test_ventes_annulees_brouillons_et_hors_periode_exclus(self):
        qs = sales_queryset_for_seller(
            self.company_a, self.vendeur1, self.fenetre_debut, self.fenetre_fin
        )
        references = set(qs.values_list('reference', flat=True))
        for exclue in ('POS-V1-ANNULEE', 'POS-V1-BROUILLON', 'POS-V1-VIEILLE', 'POS-SANS-VENDEUR'):
            self.assertNotIn(exclue, references)

    def test_le_vendeur2_ne_voit_que_ses_ventes(self):
        qs = sales_queryset_for_seller(
            self.company_a, self.vendeur2, self.fenetre_debut, self.fenetre_fin
        )
        self.assertEqual(sorted(qs.values_list('reference', flat=True)), ['POS-V2-001'])

    def test_exploitation_inter_entreprise(self):
        qs = sales_queryset_for_seller(
            self.company_a, self.vendeur2, self.fenetre_debut, self.fenetre_fin
        )
        self.assertNotIn('POS-V2-AUTRE', set(qs.values_list('reference', flat=True)))

    # ------------------------------------------------ 2. resolve_seller --

    def test_resolve_seller_identifie_le_bon_compte(self):
        cibles = [
            str(self.vendeur1.id),               # identifiant technique
            'awa.traore@alpha.com',              # email exact
            'AWA.TRAORE@ALPHA.COM',              # email insensible à la casse
            'awa.traore',                        # email partiel (compatibilité)
            'Awa Traore',                        # nom complet
        ]
        for cible in cibles:
            vendeur, erreur = resolve_seller(self.company_a, cible)
            self.assertIsNone(erreur, 'Cible %s : aucune erreur attendue' % cible)
            self.assertEqual(vendeur, self.vendeur1, 'Cible %s' % cible)

    def test_resolve_seller_refuse_un_vendeur_inconnu(self):
        vendeur, erreur = resolve_seller(self.company_a, 'personne.inconnue@alpha.com')
        self.assertIsNone(vendeur)
        self.assertIsNotNone(erreur)

    def test_resolve_seller_refuse_un_email_partiel_ambigu(self):
        """Deux vendeurs dont l'email contient le même fragment : refus, pas de choix arbitraire."""
        User.objects.create_user(
            email='awa.traore2@alpha.com',
            password='Password123!',
            first_name='Awa',
            last_name='Traore Bis',
            company=self.company_a,
            role=UserRole.CASHIER,
        )
        vendeur, erreur = resolve_seller(self.company_a, 'awa.traore')
        self.assertIsNone(vendeur)
        self.assertIsNotNone(erreur)

    def test_resolve_seller_refuse_un_vendeur_d_une_autre_entreprise(self):
        vendeur, erreur = resolve_seller(self.company_a, str(self.user_b.id))
        self.assertIsNone(vendeur)
        self.assertIsNotNone(erreur)

        vendeur, erreur = resolve_seller(self.company_a, 'admin@beta.com')
        self.assertIsNone(vendeur)
        self.assertIsNotNone(erreur)

    # ------------------------------------------------- 3. export PDF ----

    def test_export_pdf_du_vendeur_choisi(self):
        reponse = self.client_vendeur1.get(
            URL_EXPORT, {'start_date': self.debut, 'end_date': self.fin,
                         'seller_id': str(self.vendeur1.id)}
        )
        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(reponse['Content-Type'], 'application/pdf')
        nom = self._nom_fichier(reponse)
        self.assertIn('Awa_Traore', nom)
        self.assertNotIn('Boubacar', nom)

    def test_export_pdf_vendeur2_ne_contient_pas_le_vendeur1(self):
        reponse = self.client_a.get(
            URL_EXPORT, {'start_date': self.debut, 'end_date': self.fin,
                         'seller_id': str(self.vendeur2.id)}
        )
        self.assertEqual(reponse.status_code, 200)
        nom = self._nom_fichier(reponse)
        self.assertIn('Boubacar_Kone', nom)
        self.assertNotIn('Awa', nom)

    def test_export_pdf_vendeur_inconnu_renvoie_404(self):
        import json

        reponse = self.client_a.get(
            URL_EXPORT, {'start_date': self.debut, 'end_date': self.fin,
                         'seller_id': '00000000-0000-0000-0000-000000000000'}
        )
        self.assertEqual(reponse.status_code, 404)
        self.assertIn('detail', json.loads(reponse.content.decode('utf-8')))

        reponse = self.client_a.get(
            URL_EXPORT, {'start_date': self.debut, 'end_date': self.fin,
                         'seller': 'inconnu@alpha.com'}
        )
        self.assertEqual(reponse.status_code, 404)

    def test_export_pdf_avec_email_exact(self):
        reponse = self.client_a.get(
            URL_EXPORT, {'start_date': self.debut, 'end_date': self.fin,
                         'seller': 'boubacar.kone@alpha.com'}
        )
        self.assertEqual(reponse.status_code, 200)
        self.assertIn('Boubacar_Kone', self._nom_fichier(reponse))

    def test_caissier_limite_a_son_propre_bilan(self):
        """Un caissier qui demande le bilan d'un collègue obtient le sien."""
        reponse = self.client_vendeur1.get(
            URL_EXPORT, {'start_date': self.debut, 'end_date': self.fin,
                         'seller_id': str(self.vendeur2.id)}
        )
        self.assertEqual(reponse.status_code, 200)
        nom = self._nom_fichier(reponse)
        self.assertIn('Awa_Traore', nom)
        self.assertNotIn('Boubacar', nom)

    def test_export_sans_parametre_repond_toujours(self):
        reponse = self.client_a.get(URL_EXPORT, {'start_date': self.debut, 'end_date': self.fin})
        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(reponse['Content-Type'], 'application/pdf')
