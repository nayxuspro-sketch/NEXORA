"""
La liste des ventes doit montrer les ventes du jour, des leur enregistrement.

Verifie le chemin exact utilise par l'ecran /sales/ :
    GET /api/v1/sales/?page=1&search=

Ce test existe parce qu'un ecran affichait des ventes fictives quand la
requete echouait : il verrouille le fait que, cote serveur, une vente
enregistree au POS est immediatement visible dans la liste, en tete.

Lancer :

    py manage.py test tests.test_liste_ventes_du_jour -v 2
"""

from decimal import Decimal

from django.utils import timezone
from rest_framework import status

from apps.sales.models import Sale
from apps.sales.services import SaleService
from tests.test_nexora_backend import BaseNexoraTestCase


class ListeVentesDuJourTests(BaseNexoraTestCase):
    """La vente du jour apparait dans la liste, en tete, avec ses montants."""

    def test_la_vente_du_jour_apparait_dans_la_liste(self):
        """Vente enregistree a l'instant : presente dans la liste paginee."""
        vente = SaleService.create_and_complete_sale(
            company=self.company_a, store=self.store_a, seller=self.user_a,
            items_data=[{'product': self.product_a1, 'quantity': Decimal('2.00'),
                         'unit_price': Decimal('800.00'), 'tax_rate': Decimal('20.00')}],
        )
        vente.refresh_from_db()
        self.assertEqual(vente.total_amount, Decimal('1920.00'))

        reponse = self.client_a.get('/api/v1/sales/', {'page': 1, 'search': ''})
        self.assertEqual(reponse.status_code, status.HTTP_200_OK, reponse.content[:300])

        references = [ligne['reference'] for ligne in reponse.data['results']]
        self.assertIn(vente.reference, references,
                      'la vente du jour est absente de la liste : %s' % references)
        # la plus recente est en tete (tri par date decroissante)
        self.assertEqual(references[0], vente.reference)

        ligne = reponse.data['results'][references.index(vente.reference)]
        self.assertEqual(Decimal(ligne['total_amount']), Decimal('1920.00'))
        self.assertEqual(Decimal(ligne['paid_amount']), Decimal('0.00'))

    def test_la_liste_ne_contient_que_les_ventes_de_l_entreprise(self):
        """La liste est filtree par entreprise : aucune fuite entre clients."""
        SaleService.create_and_complete_sale(
            company=self.company_a, store=self.store_a, seller=self.user_a,
            items_data=[{'product': self.product_a1, 'quantity': Decimal('1.00'),
                         'unit_price': Decimal('800.00'), 'tax_rate': Decimal('20.00')}],
        )
        reponse = self.client_a.get('/api/v1/sales/', {'page': 1})
        self.assertEqual(reponse.status_code, status.HTTP_200_OK)
        for ligne in reponse.data['results']:
            self.assertEqual(str(ligne['company']), str(self.company_a.id))
