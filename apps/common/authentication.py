from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import exceptions
import logging

logger = logging.getLogger('nexora.auth')

class OptionalJWTAuthentication(JWTAuthentication):
    """
    Authentifie l'utilisateur via JWT si un token valide est fourni.
    Si le token est invalide, corrompu, expiré ou issu d'une session locale de secours,
    au lieu de lever une exception 401 bloquante (AuthenticationFailed),
    cette classe ignore gracieusement l'erreur et laisse la requête continuer.
    Ainsi, les formulaires d'enregistrement et la caisse ne sont JAMAIS bloqués par une erreur 401 !
    """
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
        except Exception as e:
            # Token invalide, faux ou expiré : ne pas lever d'erreur 401
            # Laisser la requête continuer en tant qu'utilisateur local/anonyme
            logger.info(f"Token JWT non valide ignoré avec succès: {e}")
            return None
