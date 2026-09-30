from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging
import traceback

logger = logging.getLogger('nexora.errors')


def custom_exception_handler(exc, context):
    """
    Standardized API exception format across the entire NEXORA platform.
    """
    response = exception_handler(exc, context)

    if response is not None:
        error_payload = {
            "status": "error",
            "code": getattr(exc, 'default_code', 'api_error'),
            "message": "Une erreur de validation ou de requête s'est produite.",
            "details": response.data
        }

        if response.status_code == 404:
            error_payload["message"] = "Ressource introuvable."
            error_payload["code"] = "not_found"
        elif response.status_code == 403:
            error_payload["message"] = "Accès refusé. Vous n'avez pas les permissions requises."
            error_payload["code"] = "permission_denied"
        elif response.status_code == 401:
            error_payload["message"] = "Non authentifié ou jeton expiré."
            error_payload["code"] = "not_authenticated"
        elif response.status_code == 400:
            error_payload["message"] = "Données invalides ou règles métier non respectées."
            error_payload["code"] = "validation_error"

        response.data = error_payload
        return response

    # Unhandled server errors (500)
    tb = traceback.format_exc()
    print(f"\n[EXCEPTION 500 CAPTURED] Context: {context}\nException: {exc}\nTraceback:\n{tb}\n", flush=True)

    return Response(
        {
            "status": "error",
            "code": "server_error",
            "message": f"Erreur interne : {str(exc)}",
            "details": tb
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
