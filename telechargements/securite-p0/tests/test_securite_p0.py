"""
Tests de securite du palier P0 (poste de caisse local / appels distants).

Chaque test reproduit une attaque reellement possible avant correction, puis
verifie la reponse. Deux principes :

1. un appel recu depuis une AUTRE machine (adresse non locale) sans jeton valide
   doit etre refuse ;
2. un appel provenant du POSTE de caisse lui-meme doit continuer a fonctionner
   exactement comme avant (boutons PDF, onglets, caisse hors-ligne).

Lancer :

    py manage.py test tests.test_securite_p0 -v 2
"""

from django.core.cache import cache
from django.test import override_settings
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.companies.models import Company
from apps.accounts.models import User, UserRole
from apps.catalog.models import Product
from apps.inventory.models import Store
from tests.test_nexora_backend import BaseNexoraTestCase

POSTE = '127.0.0.1'            # le poste de caisse
DISTANT = '192.168.1.50'       # un autre poste du reseau / Internet


class SecuriteP0Tests(BaseNexoraTestCase):
    """Palier P0 : fermer les acces distants sans rien changer sur le poste."""

    def setUp(self):
        super().setUp()
        # Clients anonymes selon leur provenance.
        self.anonyme_poste = APIClient()
        self.anonyme_distant = APIClient()

        # Un caissier (role sans droit sur le journal d'audit).
        self.caissier = User.objects.create_user(
            email='caissier.secu@alpha.com',
            password='Password123!',
            company=self.company_a,
            role=UserRole.CASHIER,
        )
        # Un vrai jeton JWT dans l'en-tete, comme le fait l'application :
        # force_authenticate() court-circuite le niveau vue et ne represente pas
        # ce que recoit reellement le serveur.
        self.client_admin_a = self._client_avec_jeton(self.user_a)
        self.client_caissier = self._client_avec_jeton(self.caissier)
        self.client_admin_b = self._client_avec_jeton(self.user_b)

    @staticmethod
    def _client_avec_jeton(utilisateur):
        client = APIClient()
        jeton = RefreshToken.for_user(utilisateur).access_token
        client.credentials(HTTP_AUTHORIZATION='Bearer %s' % jeton)
        return client

    # ------------------------------------------------------------------ outils
    def _poste(self, client, chemin, **extra):
        return client.get(chemin, REMOTE_ADDR=POSTE, **extra)

    def _distant(self, client, chemin, **extra):
        return client.get(chemin, REMOTE_ADDR=DISTANT, **extra)

    # ------------------------------------------------- 1. appels distants nus
    def test_appel_anonyme_distant_refuse(self):
        """Un appel sans jeton depuis le reseau ne doit plus lire les donnees."""
        reponse = self._distant(self.anonyme_distant, '/api/v1/products/')
        self.assertIn(reponse.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))
        self.assertNotIn(b'LAPTOP-01', reponse.content)

    def test_appel_anonyme_distant_refuse_sur_les_ventes(self):
        """Les ventes de la premiere entreprise ne sont plus livrees a distance."""
        reponse = self._distant(self.anonyme_distant, '/api/v1/sales/')
        self.assertIn(reponse.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_liste_des_comptes_inaccessible_a_distance(self):
        """Avant : /api/v1/users/ repondait 200 a n'importe qui (comptes exposes)."""
        reponse = self._distant(self.anonyme_distant, '/api/v1/users/')
        self.assertIn(reponse.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))
        self.assertNotIn(b'admin@alpha.com', reponse.content)

        reponse = self._distant(self.anonyme_distant, '/api/v1/groups/')
        self.assertIn(reponse.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_creation_de_compte_a_distance_impossible(self):
        """Avant : un appel distant pouvait creer un compte (meme administrateur)."""
        avant = User.objects.count()
        reponse = self.anonyme_distant.post('/api/v1/users/', {
            'email': 'intrus@alpha.com',
            'password': 'Password123!',
            'role': UserRole.ADMIN,
            'first_name': 'Intrus',
            'last_name': 'Reseau',
        }, format='json', REMOTE_ADDR=DISTANT)
        self.assertIn(reponse.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))
        self.assertEqual(User.objects.count(), avant)
        self.assertFalse(User.objects.filter(email='intrus@alpha.com').exists())

    def test_export_pdf_refuse_a_distance(self):
        """Les exports PDF (documents comptables) ne sortent plus du reseau."""
        reponse = self._distant(self.anonyme_distant, '/api/v1/reports/export-bi-pdf/')
        self.assertIn(reponse.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_appel_relaye_par_le_proxy_avec_adresse_distante_refuse(self):
        """Un poste du reseau passe par le relais Next.js : il reste distant."""
        reponse = self.anonyme_distant.get(
            '/api/v1/products/',
            REMOTE_ADDR=POSTE,
            HTTP_X_FORWARDED_FOR=DISTANT,
        )
        self.assertIn(reponse.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_garde_couvre_les_vues_declarees_allowany(self):
        """Les vues marquees AllowAny (licences, releases) sont couvertes aussi."""
        for chemin in ('/api/v1/store-licenses/', '/api/v1/settings/permissions/'):
            with self.subTest(chemin=chemin):
                reponse = self._distant(self.anonyme_distant, chemin)
                self.assertIn(reponse.status_code,
                              (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN), chemin)

    # ------------------------------------------------- 2. le poste continue
    def test_poste_de_caisse_anonyme_continue_de_fonctionner(self):
        """Parcours de caisse hors-ligne : les ecrans doivent repondre comme avant."""
        for chemin in ('/api/v1/products/', '/api/v1/sales/', '/api/v1/registers/',
                       '/api/v1/stock-levels/', '/api/v1/stores/'):
            with self.subTest(chemin=chemin):
                reponse = self._poste(self.anonyme_poste, chemin)
                self.assertEqual(reponse.status_code, status.HTTP_200_OK, chemin)

    def test_export_pdf_depuis_le_poste_fonctionne_toujours(self):
        """Le bouton PDF ouvre un onglet sans jeton : depuis le poste, il marche."""
        reponse = self._poste(self.anonyme_poste, '/api/v1/reports/export-bi-pdf/')
        self.assertEqual(reponse.status_code, status.HTTP_200_OK)
        self.assertIn('application/pdf', reponse['Content-Type'])

    def test_jeton_invalide_depuis_le_poste_reste_ignore(self):
        """Inchange : sur le poste, un jeton perime ne bloque pas la caisse."""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Bearer jeton.abime.local')
        reponse = client.get('/api/v1/products/', REMOTE_ADDR=POSTE)
        self.assertEqual(reponse.status_code, status.HTTP_200_OK)

    def test_jeton_invalide_a_distance_refuse(self):
        """Avant : jeton invalide ignore -> appelant anonyme -> donnees servies."""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Bearer jeton.abime.distant')
        reponse = client.get('/api/v1/products/', REMOTE_ADDR=DISTANT)
        self.assertIn(reponse.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))
        self.assertNotIn(b'LAPTOP-01', reponse.content)

    def test_mode_caisse_locale_desactivable(self):
        """NEXORA_CAISSE_LOCALE=False : meme le poste doit presenter un jeton."""
        with override_settings(NEXORA_CAISSE_LOCALE=False):
            reponse = self._poste(self.anonyme_poste, '/api/v1/products/')
            self.assertIn(reponse.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    # ------------------------------------------------- 3. utilisateurs reconnus
    def test_utilisateur_authentifie_conserve_ses_acces(self):
        """Aucun changement pour un utilisateur connecte : ses donnees restent la."""
        reponse = self.client_admin_a.get('/api/v1/products/', REMOTE_ADDR=DISTANT)
        self.assertEqual(reponse.status_code, status.HTTP_200_OK)

    def test_cloisonnement_entre_entreprises_maintenu(self):
        """L'utilisateur de l'entreprise B ne voit que les produits de B."""
        reponse = self.client_admin_b.get('/api/v1/products/', REMOTE_ADDR=DISTANT)
        self.assertEqual(reponse.status_code, status.HTTP_200_OK)
        self.assertNotIn(b'LAPTOP-01', reponse.content)

    def test_journal_audit_reserve_aux_roles_declares(self):
        """`required_roles` (ADMIN/MANAGER/AUDITOR) est enfin applique."""
        reponse = self.client_caissier.get('/api/v1/audit-logs/', REMOTE_ADDR=DISTANT)
        self.assertEqual(reponse.status_code, status.HTTP_403_FORBIDDEN)

        reponse = self.client_admin_a.get('/api/v1/audit-logs/', REMOTE_ADDR=DISTANT)
        self.assertEqual(reponse.status_code, status.HTTP_200_OK)

    # ------------------------------------------------- 4. fuites de diagnostic
    @override_settings(DEBUG=True)
    def test_page_de_diagnostic_masquee_pour_un_appel_distant(self):
        """En DEBUG, la page 404 bavarde de Django ne doit pas sortir du poste."""
        reponse = self._distant(self.anonyme_distant, '/url-qui-nexiste-pas/')
        self.assertEqual(reponse.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('application/json', reponse['Content-Type'])
        self.assertNotIn(b'urlpatterns', reponse.content)
        self.assertNotIn(b'SETTINGS', reponse.content)

    @override_settings(DEBUG=True)
    def test_url_api_inconnue_refusee_a_distance(self):
        """Une URL d'API inconnue est refusee avant meme d'atteindre le routeur."""
        reponse = self._distant(self.anonyme_distant, '/api/v1/url-qui-nexiste-pas/')
        self.assertEqual(reponse.status_code, status.HTTP_401_UNAUTHORIZED)

    @override_settings(DEBUG=True)
    def test_page_de_diagnostic_conservee_sur_le_poste(self):
        """Sur le poste, la page 404 de diagnostic reste disponible (inchange)."""
        reponse = self._poste(self.anonyme_poste, '/url-qui-nexiste-pas/')
        self.assertEqual(reponse.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('text/html', reponse['Content-Type'])

    # ------------------------------------------------- 5. navigateur et CORS
    def test_origine_publique_refusee_par_le_cors(self):
        """Une page web quelconque ne peut plus lire l'API via le navigateur."""
        reponse = self.anonyme_poste.get(
            '/api/v1/products/', REMOTE_ADDR=POSTE,
            HTTP_ORIGIN='https://site-malveillant.example',
        )
        self.assertNotIn('Access-Control-Allow-Origin', reponse)

    def test_origine_locale_acceptee_par_le_cors(self):
        """Le frontend local (npm run dev) continue d'etre autorise."""
        reponse = self.anonyme_poste.get(
            '/api/v1/products/', REMOTE_ADDR=POSTE, HTTP_ORIGIN='http://localhost:3000',
        )
        self.assertEqual(reponse['Access-Control-Allow-Origin'], 'http://localhost:3000')

    # ------------------------------------------------- 6. force brute
    def test_connexion_limitee_en_frequence(self):
        """La connexion ne peut plus etre essayee en boucle sans limite (10/min)."""
        cache.clear()
        codes = []
        for _ in range(11):
            reponse = self.anonyme_poste.post(
                '/api/v1/auth/token/',
                {'email': 'inconnu@alpha.com', 'password': 'MauvaisMotDePasse!'},
                format='json', REMOTE_ADDR=POSTE,
            )
            codes.append(reponse.status_code)
        self.assertEqual(codes[-1], status.HTTP_429_TOO_MANY_REQUESTS, codes)
        cache.clear()
