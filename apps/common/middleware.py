import logging

from django.conf import settings
from django.http import JsonResponse
from django.middleware.clickjacking import XFrameOptionsMiddleware

from .acces import est_client_local

logger = logging.getLogger('nexora.securite')


class FrameOptionsMiddleware(XFrameOptionsMiddleware):
    """
    Subclasses Django's XFrameOptionsMiddleware.
    Keeps standard SAMEORIGIN clickjacking protection for standard web pages,
    while removing X-Frame-Options or setting it permissive for PDF export
    endpoints and binary documents to ensure they preview seamlessly in embedded
    viewers and webviews.
    """
    def process_response(self, request, response):
        content_type = response.get('Content-Type', '')
        if (
            'pdf' in request.path
            or 'export' in request.path
            or 'application/pdf' in content_type
            or 'octet-stream' in content_type
        ):
            # Exempt PDF endpoints from framing restrictions
            if 'X-Frame-Options' in response:
                del response['X-Frame-Options']
            return response

        return super().process_response(request, response)


class DebugLocalSeulementMiddleware:
    """En DEBUG, les pages de diagnostic Django restent sur le poste.

    En mode DEBUG, Django affiche des pages tres bavardes (trace complete,
    extraits de configuration, liste des routes) pour les erreurs 404 et 500.
    Depuis le poste, c'est utile : c'est ce qui permet de copier une trace en cas
    de probleme. Depuis une autre machine, c'est une fuite d'information.

    Cette couche remplace donc ces pages par une erreur neutre UNIQUEMENT quand
    la requete ne vient pas du poste. Le detail complet reste ecrit dans la
    console du serveur.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def _masquer(self, request):
        return bool(getattr(settings, 'DEBUG', False)) and not est_client_local(request)

    @staticmethod
    def _erreur_neutre(statut):
        if statut == 404:
            charge = {
                'status': 'error',
                'code': 'not_found',
                'message': "Ressource introuvable.",
                'details': None,
            }
        else:
            charge = {
                'status': 'error',
                'code': 'server_error',
                'message': "Une erreur interne s'est produite sur le serveur NEXORA.",
                'details': None,
            }
        return JsonResponse(charge, status=statut)

    def __call__(self, request):
        if not self._masquer(request):
            return self.get_response(request)

        try:
            response = self.get_response(request)
        except Exception:
            logger.exception("Exception sur un appel distant : page de diagnostic masquee.")
            return self._erreur_neutre(500)

        if response.status_code in (404, 500) and 'text/html' in response.get('Content-Type', ''):
            logger.info("Page de diagnostic Django masquee pour un appel distant (%s).", response.status_code)
            return self._erreur_neutre(response.status_code)

        return response


class GardeReseauMiddleware:
    """Une seule regle pour toute l'API : un appel anonyme venu du reseau est refuse.

    La regle est volontairement posee ici, en un seul endroit, plutot que dans
    chaque vue : les exports PDF, les licences et les telechargements declaraient
    `AllowAny` (le lien direct n'envoie pas de jeton), et un appelant distant
    pouvait donc lire ces documents. Verifier ici couvre TOUTES les routes
    `/api/v1/`, y compris celles qui seront ajoutees plus tard.

    Trois cas passes :
    - utilisateur reconnu (session ouverte, ou jeton JWT valide) ;
    - requete venant du poste de caisse lui-meme (mode hors-ligne) ;
    - routes de connexion et de sante, necessairement accessibles sans jeton.
    """

    # Routes accessibles sans jeton : connexion, rafraichissement, sante.
    CHEMINS_PUBLICS = ('/api/v1/auth/token/', '/api/v1/health/')

    message = ("Authentification requise : les appels sans jeton ne sont acceptes "
               "que depuis le poste de caisse lui-meme.")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not self._concerne(request):
            return self.get_response(request)
        if est_client_local(request) or self._appelant_reconnu(request):
            return self.get_response(request)

        logger.warning(
            "Appel anonyme refuse depuis %s : %s", request.META.get('REMOTE_ADDR'), request.path,
        )
        return JsonResponse({
            'status': 'error',
            'code': 'not_authenticated',
            'message': self.message,
            'details': None,
        }, status=401)

    @classmethod
    def _concerne(cls, request):
        chemin = request.path
        if not chemin.startswith('/api/v1/'):
            return False
        return not chemin.startswith(cls.CHEMINS_PUBLICS)

    @staticmethod
    def _appelant_reconnu(request):
        """Session Django ouverte, ou jeton JWT valide presente dans l'en-tete."""
        utilisateur = getattr(request, 'user', None)
        if utilisateur is not None and utilisateur.is_authenticated:
            return True

        from .authentication import OptionalJWTAuthentication
        try:
            authentification = OptionalJWTAuthentication().authenticate(request)
        except Exception:
            return False
        return authentification is not None
