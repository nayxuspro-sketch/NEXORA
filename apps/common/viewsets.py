import logging

from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied

from .acces import caisse_locale_active, est_client_local
from .permissions import IsAuthenticatedAndInTenant

logger = logging.getLogger('nexora.tenants')


class TenantModelViewSet(viewsets.ModelViewSet):
    """
    Base viewset for all multi-tenant entities.
    - Restricts querysets strictly to the active company.
    - Automatically injects user's company upon record creation.
    - Prevents cross-tenant data leaks.

    L'entreprise retenue provient de l'utilisateur authentifie. Pour un appel
    anonyme, elle n'est deduite de la base QUE si la requete vient du poste de
    caisse lui-meme : auparavant, n'importe quel appelant anonyme lisait - et
    pouvait meme creer - les donnees de la premiere entreprise.
    """

    permission_classes = [IsAuthenticatedAndInTenant]

    def get_company(self):
        request = self.request
        utilisateur = getattr(request, 'user', None)

        # 1) Appel authentifie : l'entreprise de l'utilisateur fait foi (inchange).
        if utilisateur is not None and utilisateur.is_authenticated:
            entreprise = getattr(utilisateur, 'company', None)
            if entreprise is not None:
                return entreprise
            logger.warning(
                "Utilisateur authentifie sans entreprise (id=%s) : repli sur la "
                "premiere entreprise.", getattr(utilisateur, 'id', None),
            )
            return self._premiere_entreprise()

        # 2) Appel anonyme : uniquement depuis le poste de caisse local.
        if not (caisse_locale_active() and est_client_local(request)):
            raise PermissionDenied(
                "Acces refuse : les appels sans jeton ne sont acceptes que depuis "
                "le poste de caisse lui-meme."
            )
        return self._premiere_entreprise()

    @staticmethod
    def _premiere_entreprise():
        from apps.companies.models import Company
        entreprise = Company.objects.first()
        if entreprise is None:
            entreprise = Company.objects.create(
                name="NEXORA BURKINA COMMERCIAL GROUP", currency="XOF",
            )
            logger.warning("Aucune entreprise en base : creation d'une entreprise par defaut.")
        return entreprise

    def get_queryset(self):
        qs = super().get_queryset()
        company = self.get_company()
        if company:
            return qs.filter(company=company)
        return qs

    def perform_create(self, serializer):
        serializer.save(company=self.get_company())
