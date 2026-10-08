"""
Integrite des ventes : la caisse et le client ne doivent pas etre substitues.

Meme regle que pour le magasin et l'article (correctif precedant) : un
identifiant fourni qui n'appartient pas a VOTRE entreprise doit etre refuse,
jamais remplace en silence par le premier element du catalogue.

Consequences du defaut, en clair :
  - la vente peut etre rattachee a la CAISSE d'une autre entreprise (ou a la
    premiere caisse venue), donc etre comptee dans la cloture d'une autre
    caisse et fausser le rapport Z ;
  - la vente peut etre rattachee au mauvais CLIENT : le bilan du client, ses
    creances et son historique sont faux.

Lancer :

    py manage.py test tests.test_integrite_caisse_client -v 2
"""

from rest_framework import status

from apps.partners.models import Partner, PartnerType
from apps.pos.models import CashRegister
from apps.sales.models import Sale
from tests.test_nexora_backend import BaseNexoraTestCase


class IntegriteCaisseClientTests(BaseNexoraTestCase):
    def setUp(self):
        super().setUp()
        self.caisse_a = CashRegister.objects.create(
            company=self.company_a, store=self.store_a, name='Caisse A1', code='CAISSE-A1',
        )
        self.caisse_b = CashRegister.objects.create(
            company=self.company_b, store=self.store_b, name='Caisse B1', code='CAISSE-B1',
        )
        self.client_b = Partner.objects.create(
            company=self.company_b, name='Client Beta', partner_type=PartnerType.CUSTOMER,
        )

    def _vente(self, **extra):
        charge = {
            'store': str(self.store_a.id),
            'items': [{'product': str(self.product_a1.id), 'quantity': 1}],
        }
        charge.update(extra)
        return self.client_a.post('/api/v1/sales/', charge, format='json')

    def test_caisse_d_une_autre_entreprise_refusee(self):
        """La caisse de l'entreprise B ne peut pas encaisser une vente de A."""
        reponse = self._vente(register=str(self.caisse_b.id))
        self.assertEqual(reponse.status_code, status.HTTP_400_BAD_REQUEST, reponse.content[:300])
        self.assertEqual(Sale.objects.filter(company=self.company_a).count(), 0)

    def test_client_d_une_autre_entreprise_refuse(self):
        """La vente de A ne peut pas etre imputee a un client de B."""
        reponse = self._vente(customer=str(self.client_b.id))
        self.assertEqual(reponse.status_code, status.HTTP_400_BAD_REQUEST, reponse.content[:300])
        self.assertEqual(Sale.objects.filter(company=self.company_a).count(), 0)

    def test_vente_avec_sa_caisse_et_son_client_acceptee(self):
        """Le parcours normal reste inchange : 201, avec la bonne caisse et le bon client."""
        reponse = self._vente(register=str(self.caisse_a.id), customer=str(self.customer_a.id))
        self.assertEqual(reponse.status_code, status.HTTP_201_CREATED, reponse.content[:300])
        vente = Sale.objects.get(company=self.company_a)
        self.assertEqual(vente.register_id, self.caisse_a.id)
        self.assertEqual(vente.customer_id, self.customer_a.id)

    def test_vente_sans_client_toujours_acceptee(self):
        """Vente comptoir (client non precise) : toujours 201."""
        reponse = self._vente(register=str(self.caisse_a.id), customer=None)
        self.assertEqual(reponse.status_code, status.HTTP_201_CREATED, reponse.content[:300])
