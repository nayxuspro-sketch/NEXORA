"""
« ETAT DE VENTE INDIVIDUEL DU VENDEUR » : le PDF doit dire la verite.

Le bouton du POS (« Rapport Individuel Vendeur », 2 pages) appelle :

    /api/v1/sales/export-seller-pdf/?start_date=...&end_date=...&seller=<email>

Ce que ces tests verrouillent, sur un jeu de donnees controle :
  1. la periode demandee est respectee : une periode passee ne doit pas
     contenir les ventes d'aujourd'hui ;
  2. seules les ventes du vendeur demande apparaissent ;
  3. sans vendeur precise, un caissier ne voit que son propre bilan ;
  4. une vente annulee ne compte pas dans le chiffre d'affaires.

Le PDF est lu sans bibliotheque supplementaire : les flux sont decodes
(ASCII85 + Flate) avec la bibliotheque standard de Python.

Lancer :

    py manage.py test tests.test_etat_vendeur_pdf -v 2
"""

import base64
import re
import zlib

from decimal import Decimal

from django.utils import timezone

from apps.accounts.models import User, UserRole
from apps.sales.models import Sale
from tests.test_nexora_backend import BaseNexoraTestCase

RAPPORT = '/api/v1/sales/export-seller-pdf/'


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

    def test_une_vente_annulee_ne_compte_pas(self):
        """Vente annulee : elle disparait du chiffre d'affaires du rapport."""
        texte_avant = self._rapport(self.user_a, seller='awa@alpha.com')
        self._doit_contenir(texte_avant, b'V-ALPHA-AUJOURD', 'vente du jour manquante')

        Sale.objects.filter(id=self.vente_du_jour.id).update(status='CANCELLED')

        texte_apres = self._rapport(self.user_a, seller='awa@alpha.com')
        self._ne_doit_pas_contenir(texte_apres, b'V-ALPHA-AUJOURD',
                                   'une vente annulee apparait encore dans le rapport')
