"""
« ETAT DE VENTE INDIVIDUEL DU VENDEUR » : le PDF doit dire toute la verite.

Le bouton du POS (« Mon Bilan Vente PDF », nombre de pages variable) appelle :

    /api/v1/sales/export-seller-pdf/?start_date=...&end_date=...&seller=<email>

Ce que ces tests verrouillent, sur un jeu de donnees controle :
  1. la periode demandee est respectee : une periode passee ne doit pas
     contenir les ventes d'aujourd'hui ;
  2. seules les ventes du vendeur demande apparaissent ;
  3. sans vendeur precise, un caissier ne voit que son propre bilan ;
  4. une vente annulee ne compte pas dans le chiffre d'affaires ;
  5. le PDF n'est pas limite aux six produits les plus vendus ;
  6. chaque produit reste distingue par son identifiant, meme si deux noms sont identiques ;
  7. les totaux encaisses, taxes, remises et quantites sont affiches.

Le PDF est lu sans bibliotheque supplementaire : les flux sont decodes
(ASCII85 + Flate) avec la bibliotheque standard de Python.

Lancer :

    py manage.py test tests.test_etat_vendeur_pdf -v 2
"""

import base64
import re
import zlib

from decimal import Decimal
from types import SimpleNamespace
import unittest

from django.utils import timezone

from apps.accounts.models import User, UserRole
from apps.catalog.models import Product
from apps.sales.models import Sale, SaleItem, SaleStatus
from apps.sales.pdf_seller_report import (
    _nexora_agreger_articles,
    _nexora_formater_quantite,
    _nexora_produits_tries,
)
from tests.test_nexora_backend import BaseNexoraTestCase

RAPPORT = '/api/v1/sales/export-seller-pdf/'


class _RelationLignes:
    def __init__(self, lignes):
        self.lignes = lignes

    def all(self):
        return self.lignes


class AgregationArticlesPdfTests(unittest.TestCase):
    """Tests purs des totaux produit utilises par le vrai generateur PDF."""

    def test_huit_produits_et_deux_noms_identiques_restent_distincts(self):
        lignes = []
        for numero in range(1, 9):
            # Deux références distinctes portent volontairement le même nom.
            nom = 'Produit identique' if numero in (1, 2) else 'Produit %02d' % numero
            produit = SimpleNamespace(
                pk='produit-%02d' % numero,
                name=nom,
                sku='SKU-COMPLET-%02d' % numero,
                cost_price=Decimal('100.00'),
            )
            lignes.append(SimpleNamespace(
                product=produit,
                quantity=Decimal('1.25'),
                total=Decimal('250.00'),
            ))

        stats, quantite_totale, cout_total = _nexora_agreger_articles(
            [SimpleNamespace(items=_RelationLignes(lignes))]
        )
        produits_tries = _nexora_produits_tries(stats)

        self.assertEqual(len(produits_tries), 8)
        self.assertEqual({p['sku'] for p in produits_tries},
                         {'SKU-COMPLET-%02d' % i for i in range(1, 9)})
        self.assertEqual(quantite_totale, Decimal('10.00'))
        self.assertEqual(cout_total, Decimal('1000.00'))
        self.assertEqual(
            sum((p['revenue'] for p in stats.values()), Decimal('0.00')),
            Decimal('2000.00'),
        )
        self.assertEqual(_nexora_formater_quantite(Decimal('1.25')), '1.25')


def _decompresser(donnees):
    """Flux d'un PDF -> octets clairs (Flate seul, puis ASCII85 + Flate)."""
    donnees = donnees.strip()
    candidats = [donnees]
    if donnees.endswith(b'~>'):
        candidats.append(donnees[:-2])
    for candidat in candidats:
        try:
            return zlib.decompress(candidat)
        except zlib.error:
            pass
        for adobe in (False, True):
            try:
                return zlib.decompress(base64.a85decode(candidat, adobe=adobe))
            except Exception:
                pass
    return b''


def texte_du_pdf(contenu):
    """Texte dessine dans un PDF produit par reportlab."""
    morceaux = [_decompresser(flux)
                for flux in re.findall(rb'stream\r?\n(.*?)endstream', contenu, re.S)]
    return b'\n'.join(morceau for morceau in morceaux if morceau)


class EtatVendeurPdfTests(BaseNexoraTestCase):
    """Le bilan PDF d'un vendeur ne doit contenir que SA vente, sur SA periode."""

    def setUp(self):
        super().setUp()
        self.awa = User.objects.create_user(
            email='awa@alpha.com', password='Password123!', first_name='Awa',
            last_name='Sana', company=self.company_a, role=UserRole.CASHIER)
        self.bouba = User.objects.create_user(
            email='bouba@alpha.com', password='Password123!', first_name='Bouba',
            last_name='Ouedraogo', company=self.company_a, role=UserRole.CASHIER)
        self.vente_janvier = self._vendre(self.awa, 'V-ALPHA-JANVIER', Decimal('1'),
                                          '2026-01-15 10:00')
        self.vente_bouba = self._vendre(self.bouba, 'V-BETA-JANVIER', Decimal('3'),
                                        '2026-01-16 10:00')
        self.vente_du_jour = self._vendre(self.awa, 'V-ALPHA-AUJOURD', Decimal('2'), None)

    # ------------------------------------------------------------------ outils

    def _vendre(self, vendeur, reference, quantite, moment):
        """Enregistre une vente par l'API au nom de ce vendeur, puis la date."""
        self.client_a.force_authenticate(user=vendeur)
        reponse = self.client_a.post('/api/v1/sales/', {
            'store': str(self.store_a.id),
            'items': [{
                'product': str(self.product_a1.id), 'quantity': str(quantite),
                'unit_price': '800.00', 'tax_rate': '20.00',
            }],
        }, format='json')
        self.assertEqual(reponse.status_code, 201, reponse.content[:300])
        vente = Sale.objects.get(id=reponse.data['id'])
        Sale.objects.filter(id=vente.id).update(reference=reference)
        if moment:
            quand = timezone.make_aware(timezone.datetime.strptime(moment, '%Y-%m-%d %H:%M'))
            Sale.objects.filter(id=vente.id).update(created_at=quand)
        return Sale.objects.get(id=vente.id)

    def _rapport(self, connecte, seller=None, debut='2026-01-01', fin='2026-12-31'):
        self.client_a.force_authenticate(user=connecte)
        parametres = {'start_date': debut, 'end_date': fin}
        if seller:
            parametres['seller'] = seller
        reponse = self.client_a.get(RAPPORT, parametres)
        self.assertEqual(reponse.status_code, 200, reponse.content[:300])
        return texte_du_pdf(reponse.content)

    def _doit_contenir(self, texte, marque, explication):
        self.assertTrue(marque in texte, '%s : « %s » absent du PDF'
                        % (explication, marque.decode()))

    def _ne_doit_pas_contenir(self, texte, marque, explication):
        self.assertTrue(marque not in texte, '%s : « %s » present dans le PDF'
                        % (explication, marque.decode()))

    # ------------------------------------------------------------------ tests

    def test_la_periode_demandee_est_respectee(self):
        """Janvier 2026 : le rapport ne doit pas contenir la vente du jour."""
        texte = self._rapport(self.user_a, seller='awa@alpha.com',
                              debut='2026-01-01', fin='2026-01-31')
        self._doit_contenir(texte, b'V-ALPHA-JANVIER', 'vente de janvier manquante')
        self._ne_doit_pas_contenir(texte, b'V-ALPHA-AUJOURD',
                                   "le rapport de janvier contient une vente hors periode")
        self._ne_doit_pas_contenir(texte, b'V-BETA-JANVIER',
                                   "le rapport d'Awa contient la vente de Bouba")
        # montants : janvier = 960 F ; la vente du jour (1 920 F) et celle de
        # Bouba (2 880 F) ne doivent apparaitre nulle part, meme dans les totaux
        self._doit_contenir(texte, b'960 FCFA', "chiffre d'affaires de janvier attendu")
        self._ne_doit_pas_contenir(texte, b'1 920 FCFA',
                                   'le total du rapport inclut la vente hors periode')
        self._ne_doit_pas_contenir(texte, b'2 880 FCFA',
                                   'le total du rapport inclut la vente de Bouba')

    def test_seules_les_ventes_du_vendeur_demande_apparaissent(self):
        """Awa : ses deux ventes, jamais celle de Bouba."""
        texte = self._rapport(self.user_a, seller='awa@alpha.com')
        self._doit_contenir(texte, b'V-ALPHA-JANVIER', 'vente de janvier manquante')
        self._doit_contenir(texte, b'V-ALPHA-AUJOURD', 'vente du jour manquante')
        self._ne_doit_pas_contenir(texte, b'V-BETA-JANVIER',
                                   "le rapport d'Awa contient la vente de Bouba")

    def test_sans_vendeur_precise_le_caissier_voit_son_propre_bilan(self):
        """Sans parametre seller, un caissier ne doit voir que SES ventes."""
        texte = self._rapport(self.awa, seller=None)
        self._doit_contenir(texte, b'V-ALPHA-JANVIER', 'vente de janvier manquante')
        self._ne_doit_pas_contenir(texte, b'V-BETA-JANVIER',
                                   "le bilan d'Awa contient la vente de Bouba")

    def test_pdf_affiche_toutes_les_ventes_et_tous_les_produits(self):
        """Les ventes et les articles au-dela du top six restent visibles."""
        references = []
        skus = []
        for numero in range(1, 9):
            produit = Product.objects.create(
                company=self.company_a,
                name='Article bilan complet %02d' % numero,
                sku='SKU-BILAN-COMPLET-%02d' % numero,
                category=self.product_a1.category,
                unit=self.product_a1.unit,
                cost_price=Decimal('100.00'),
                selling_price=Decimal('1000.00'),
            )
            montant = Decimal(str(numero * 1000))
            reference = 'BILAN-COMPLET-%02d' % numero
            vente = Sale.objects.create(
                company=self.company_a,
                reference=reference,
                store=self.store_a,
                seller=self.awa,
                status=SaleStatus.COMPLETED,
                payment_status='PAID',
                subtotal_amount=montant,
                total_amount=montant,
                paid_amount=montant,
            )
            SaleItem.objects.create(
                company=self.company_a,
                sale=vente,
                product=produit,
                quantity=Decimal('1.00'),
                unit_price=montant,
                tax_rate=Decimal('0.00'),
                total=montant,
            )
            references.append(reference.encode('ascii'))
            skus.append(('SKU-BILAN-COMPLET-%02d' % numero).encode('ascii'))

        texte = self._rapport(self.user_a, seller='awa@alpha.com')
        for reference in references:
            self._doit_contenir(texte, reference, 'une facture du vendeur manque')
        for sku in skus:
            self._doit_contenir(texte, sku, 'un produit du vendeur manque du PDF')

        # Ces indicateurs étaient calculés dans le backend, mais jamais rendus.
        for libelle in (b'Montant', b'Taxes', b'Remises', b'Articles vendus'):
            self._doit_contenir(texte, libelle, 'un indicateur du vendeur manque')

    def test_une_vente_annulee_ne_compte_pas(self):
        """Vente annulee : elle disparait du chiffre d'affaires du rapport."""
        texte_avant = self._rapport(self.user_a, seller='awa@alpha.com')
        self._doit_contenir(texte_avant, b'V-ALPHA-AUJOURD', 'vente du jour manquante')

        Sale.objects.filter(id=self.vente_du_jour.id).update(status='CANCELLED')

        texte_apres = self._rapport(self.user_a, seller='awa@alpha.com')
        self._ne_doit_pas_contenir(texte_apres, b'V-ALPHA-AUJOURD',
                                   'une vente annulee apparait encore dans le rapport')
