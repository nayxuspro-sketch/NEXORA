"""Tests de vérification du filtre vendeur du bilan BI (écran /reports).

À copier dans D:\\NEXORA\\tests\\test_bi_vendeur_filtre.py puis :

    python manage.py test tests.test_bi_vendeur_filtre -v 2

Les tests utilisent la même base de test que tests.test_bi_analytics.
"""

from rest_framework import status

from tests.test_nexora_backend import BaseNexoraTestCase


class BusinessIntelligenceSellerFilterTests(BaseNexoraTestCase):
    """Le paramètre seller_id doit restreindre réellement les calculs du bilan BI."""

    def test_bi_analytics_expose_les_vendeurs(self):
        """L'API renvoie la liste des vendeurs et le vendeur sélectionné."""
        response = self.client_a.get('/api/v1/reports/bi-analytics/?days=30&view=executive')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('available_sellers', response.data)
        self.assertIn('selected_seller', response.data)
        self.assertEqual(response.data['selected_seller'], '')

    def test_bi_analytics_seller_id_invalide(self):
        """Un identifiant non numérique est refusé proprement (400, pas 500)."""
        response = self.client_a.get('/api/v1/reports/bi-analytics/?days=30&view=executive&seller_id=abc')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bi_analytics_filtre_par_vendeur(self):
        """Avec seller_id, seules les ventes de ce vendeur sont comptabilisées."""
        base = self.client_a.get('/api/v1/reports/bi-analytics/?days=3650&view=executive')
        self.assertEqual(base.status_code, status.HTTP_200_OK)

        vendeurs = base.data.get('available_sellers') or []
        if not vendeurs:
            self.skipTest("Aucun vendeur rattaché à une vente dans la base de test")

        vendeur = vendeurs[0]
        response = self.client_a.get(
            '/api/v1/reports/bi-analytics/?days=3650&view=executive&seller_id=%s' % vendeur['id']
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(response.data['selected_seller']), str(vendeur['id']))

        # Toutes les lignes de performance vendeur doivent concerner ce vendeur.
        emails = [ligne['seller'] for ligne in response.data['sellers_performance']]
        for email in emails:
            self.assertEqual(email, vendeur['email'])

        # Le filtre ne peut pas augmenter le volume de ventes.
        self.assertLessEqual(
            response.data['sales_overview']['sales_count'],
            base.data['sales_overview']['sales_count'],
        )
