"""La caisse du POS doit etre rattachee a un magasin de SON entreprise.

Reproduit l'erreur signalee en caisse :

    Echec de la transaction
    Magasin introuvable dans votre entreprise

Trois regles sont verrouillees ici :

  1. le magasin d'une AUTRE entreprise est refuse (c'est le message signale) ;
  2. une caisse ne peut pas viser le magasin d'une autre entreprise (trou
     ferme par le correctif : avant, la creation passait en 201) ;
  3. le parcours normal fonctionne : creer la caisse sur son magasin,
     l'ouvrir, vendre, et retrouver la vente — y compris en n'envoyant que
     la caisse (le serveur en deduit le magasin).

Lancer :

    py manage.py test tests.test_caisse_pos_magasin -v 2
"""

from decimal import Decimal

from rest_framework import status

from tests.test_nexora_backend import BaseNexoraTestCase


class CaissePosMagasinTests(BaseNexoraTestCase):

    def test_1_magasin_d_une_autre_entreprise_refuse_avec_le_message_signe(self):
        """Le message exact signale en caisse est bien produit par le serveur."""
        reponse = self.client_a.post('/api/v1/sales/', {
            'store': str(self.store_b.id),       # magasin de l'entreprise B
            'items': [{'product': str(self.product_a1.id), 'quantity': Decimal('1.00'),
                       'unit_price': Decimal('800.00'), 'tax_rate': Decimal('20.00')}],
            'payment': {'amount': '944.00', 'method': 'CASH', 'reference': 'POS-PAY-000001'},
        }, format='json')
        self.assertEqual(reponse.status_code, status.HTTP_400_BAD_REQUEST, reponse.content[:300])
        self.assertEqual(reponse.data.get('error'), 'Magasin introuvable dans votre entreprise')

    def test_2_magasin_non_identifiant_refuse_clairement(self):
        """Un magasin qui n'est pas un identifiant reel (« store-01 ») est refuse."""
        reponse = self.client_a.post('/api/v1/sales/', {
            'store': 'store-01',                 # valeur inventee (caisse fictive)
            'register': 'reg-01',
            'items': [{'product': str(self.product_a1.id), 'quantity': Decimal('1.00'),
                       'unit_price': Decimal('800.00'), 'tax_rate': Decimal('20.00')}],
            'payment': {'amount': '944.00', 'method': 'CASH', 'reference': 'POS-PAY-000002'},
        }, format='json')
        self.assertEqual(reponse.status_code, status.HTTP_400_BAD_REQUEST, reponse.content[:300])
        self.assertIn('store', reponse.data.get('details', {}))

    def test_3_caisse_ne_peut_pas_viser_le_magasin_d_une_autre_entreprise(self):
        """Creation d'une caisse sur le magasin d'une autre entreprise : refus."""
        reponse = self.client_b.post('/api/v1/registers/', {
            'store': str(self.store_a.id),       # magasin de l'entreprise A
            'name': 'Caisse Beta',
            'code': 'REG-B1',
        }, format='json')
        self.assertEqual(reponse.status_code, status.HTTP_400_BAD_REQUEST, reponse.content[:300])

    def test_4_parcours_normal_creation_ouverture_vente(self):
        """Creer la caisse sur son magasin, l'ouvrir, vendre, retrouver la vente."""
        creation = self.client_a.post('/api/v1/registers/', {
            'store': str(self.store_a.id),
            'name': 'Caisse Comptoir Principal',
            'code': 'REG-A1',
        }, format='json')
        self.assertEqual(creation.status_code, status.HTTP_201_CREATED, creation.content[:300])
        caisse = creation.data['id']

        ouverture = self.client_a.post(
            f'/api/v1/registers/{caisse}/open_session/',
            {'opening_balance': 0}, format='json')
        self.assertIn(ouverture.status_code, (status.HTTP_200_OK, status.HTTP_201_CREATED),
                      ouverture.content[:300])

        # Le POS corrige n'envoie QUE la caisse : le serveur en deduit le magasin.
        vente = self.client_a.post('/api/v1/sales/', {
            'register': caisse,
            'items': [{'product': str(self.product_a1.id), 'quantity': Decimal('2.00'),
                       'unit_price': Decimal('800.00'), 'tax_rate': Decimal('20.00')}],
            'payment': {'amount': '1920.00', 'method': 'CASH', 'reference': 'POS-PAY-000003'},
        }, format='json')
        self.assertEqual(vente.status_code, status.HTTP_201_CREATED, vente.content[:300])
        self.assertEqual(str(vente.data['store']), str(self.store_a.id),
                         'la vente doit porter le magasin de sa caisse')
        self.assertEqual(Decimal(vente.data['total_amount']), Decimal('1920.00'))

        liste = self.client_a.get('/api/v1/sales/', {'page': 1})
        self.assertEqual(liste.status_code, status.HTTP_200_OK)
        self.assertIn(vente.data['reference'],
                      [ligne['reference'] for ligne in liste.data['results']])

    def test_5_caisse_hors_magasin_refusee_avec_un_message_precis(self):
        """Magasin et caisse fournis mais incoherents : refus explicite."""
        creation = self.client_a.post('/api/v1/registers/', {
            'store': str(self.store_a.id), 'name': 'Caisse Comptoir', 'code': 'REG-A2',
        }, format='json')
        self.assertEqual(creation.status_code, status.HTTP_201_CREATED, creation.content[:300])
        autre_magasin = self.store_a  # deuxieme magasin de la MEME entreprise

        from apps.inventory.models import StockMovementType, Store
        from apps.inventory.services import StockService
        magasin_bis = Store.objects.create(company=self.company_a, name='Annexe', code='MAG-A2')
        StockService.record_movement(
            company=self.company_a, store=magasin_bis, product=self.product_a1,
            quantity=Decimal('10.00'), movement_type=StockMovementType.INITIAL,
            reference='INIT-ANNEXE', reason='Stock initial annexe')
        reponse = self.client_a.post('/api/v1/sales/', {
            'store': str(magasin_bis.id),
            'register': creation.data['id'],      # caisse du premier magasin
            'items': [{'product': str(self.product_a1.id), 'quantity': Decimal('1.00'),
                       'unit_price': Decimal('800.00'), 'tax_rate': Decimal('20.00')}],
            'payment': {'amount': '944.00', 'method': 'CASH', 'reference': 'POS-PAY-000004'},
        }, format='json')
        self.assertEqual(reponse.status_code, status.HTTP_400_BAD_REQUEST, reponse.content[:300])
        self.assertEqual(reponse.data.get('error'), "La caisse choisie n'appartient pas a ce magasin")
        del autre_magasin

    def test_6_la_liste_des_caisses_reste_dans_l_entreprise(self):
        """L'entreprise A ne voit jamais les caisses de l'entreprise B."""
        self.client_b.post('/api/v1/registers/', {
            'store': str(self.store_b.id), 'name': 'Caisse Beta', 'code': 'REG-B2',
        }, format='json')
        reponse = self.client_a.get('/api/v1/registers/')
        self.assertEqual(reponse.status_code, status.HTTP_200_OK)
        codes = [c['code'] for c in reponse.data['results']]
        self.assertNotIn('REG-B2', codes)
