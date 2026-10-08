"""La caisse continue de fonctionner apres le correctif d'integrite des ventes.

Verifie le parcours reel : magasin, caisse, client et produit de SON entreprise.
Lancer :

    py manage.py test tests.test_vente_normale -v 2
"""

from rest_framework import status

from tests.test_nexora_backend import BaseNexoraTestCase


class VenteNormaleTests(BaseNexoraTestCase):
    def test_vente_normale_acceptee(self):
        """Magasin et produit de l'entreprise -> vente creee (201)."""
        reponse = self.client_a.post('/api/v1/sales/', {
            'store': str(self.store_a.id),
            'items': [{'product': str(self.product_a1.id), 'quantity': 1}],
        }, format='json')
        self.assertEqual(reponse.status_code, status.HTTP_201_CREATED, reponse.content[:300])

    def test_vente_avec_client_acceptee(self):
        """Avec un client de l'entreprise -> toujours 201."""
        reponse = self.client_a.post('/api/v1/sales/', {
            'store': str(self.store_a.id),
            'customer': str(self.customer_a.id),
            'items': [{'product': str(self.product_a1.id), 'quantity': 2}],
        }, format='json')
        self.assertEqual(reponse.status_code, status.HTTP_201_CREATED, reponse.content[:300])
