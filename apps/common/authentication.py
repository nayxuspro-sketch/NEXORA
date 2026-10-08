from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import exceptions
import logging

from .acces import est_client_local

logger = logging.getLogger('nexora.auth')


class OptionalJWTAuthentication(JWTAuthentication):
    """Authentifie l'utilisateur via JWT si un jeton valide est fourni.

    Sur le POSTE DE CAISSE (appel local), un jeton invalide, corrompu ou expire
    reste ignore comme avant : la caisse ne doit jamais rester bloquee sur une
    erreur 401, et les boutons PDF qui n'envoient pas de jeton doivent continuer
    de fonctionner hors-ligne.

    Pour un appel venu du RESEAU ou d'Internet, un jeton invalide est desormais
    refuse franchement (401). Avant, il etait ignore en silence et l'appelant
    devenait anonyme : il retombait alors sur les donnees de la premiere
    entreprise, sans jamais avoir a se connecter.
    """

    message = "Jeton d'authentification invalide ou expire. Reconnectez-vous."

    def authenticate(self, request):
        header = self.get_header(request)
        if header is None:
            return None

        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
            return self.get_user(validated_token), validated_token
        except Exception as erreur:
            if est_client_local(request):
                # Poste de caisse : on preserve le fonctionnement hors-ligne.
                logger.info("Jeton JWT non valide ignore (poste de caisse local) : %s", erreur)
                return None
            logger.warning("Jeton JWT non valide refuse (appel distant) : %s", erreur)
            raise exceptions.AuthenticationFailed(self.message)
