from rest_framework import permissions

from .acces import caisse_locale_active, est_client_local


def _appel_anonyme_refuse(request):
    """Vrai si l'appel est anonyme ET ne vient pas du poste de caisse."""
    return not (caisse_locale_active() and est_client_local(request))


class IsAuthenticatedAndInTenant(permissions.BasePermission):
    """
    Exige un utilisateur reconnu, SAUF depuis le poste de caisse lui-meme.

    - utilisateur authentifie : comportement inchange (le filtrage par entreprise
      est assure par les querysets de TenantModelViewSet) ;
    - appel anonyme depuis le poste : autorise (mode caisse locale hors-ligne,
      ouverture des PDF et des onglets sans jeton) ;
    - appel anonyme venu du reseau ou d'Internet : refuse.

    Auparavant cette classe renvoyait True dans tous les cas : n'importe quelle
    machine du reseau lisait donc les donnees de la premiere entreprise.
    """

    message = ("Authentification requise : les appels sans jeton ne sont acceptes "
               "que depuis le poste de caisse lui-meme.")

    def has_permission(self, request, view):
        utilisateur = getattr(request, 'user', None)
        if utilisateur is not None and utilisateur.is_authenticated:
            return True
        return not _appel_anonyme_refuse(request)

    def has_object_permission(self, request, view, obj):
        utilisateur = getattr(request, 'user', None)
        if utilisateur is None or not utilisateur.is_authenticated:
            return not _appel_anonyme_refuse(request)
        entreprise = getattr(utilisateur, 'company', None)
        if entreprise is None:
            return True
        # Aucun objet d'une autre entreprise ne doit etre accessible par identifiant.
        return getattr(obj, 'company_id', None) in (None, entreprise.id)


class AccesLocalOuAuthentifie(IsAuthenticatedAndInTenant):
    """Nom explicite pour les vues de donnees et de PDF qui etaient en AllowAny.

    Meme regle, mais l'intention est lisible sur place : le poste peut ouvrir un
    PDF ou un onglet sans jeton, un appel distant doit s'authentifier.
    """


class RolePermission(permissions.BasePermission):
    """Applique reellement les roles declares sur la vue (`required_roles`).

    Auparavant cette classe renvoyait True dans tous les cas : les roles annonces
    (par exemple ADMIN / MANAGER / AUDITOR sur le journal d'audit) n'etaient pas
    verifies. Les appels anonymes venant du poste de caisse restent autorises.
    """

    message = "Votre role ne permet pas cette operation."

    def has_permission(self, request, view):
        utilisateur = getattr(request, 'user', None)
        if utilisateur is None or not utilisateur.is_authenticated:
            return not _appel_anonyme_refuse(request)

        roles = getattr(view, 'required_roles', None)
        if not roles:
            return True
        if getattr(utilisateur, 'is_superuser', False):
            return True
        return getattr(utilisateur, 'role', None) in roles
