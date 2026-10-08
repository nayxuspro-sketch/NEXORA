"""
Qui a le droit d'appeler l'API : le poste de caisse local ou un utilisateur reconnu.

NEXORA est fait pour tourner en caisse locale, parfois sans connexion : le
navigateur du poste appelle l'API en 127.0.0.1, et certains ecrans ouvrent des
PDF ou des onglets SANS jeton (le lien direct ne transporte pas d'en-tete
d'authentification). Pour ne rien casser sur le poste, ces appels restent
autorises.

En revanche, tout ce qui arrive d'une AUTRE machine (reseau du magasin, Internet,
page web tierce relayee par le navigateur) doit presenter un jeton valide.
C'est ce module qui en decide, en un seul endroit, pour les permissions,
l'authentification et les vues.
"""

import logging

from django.conf import settings

logger = logging.getLogger('nexora.acces')

# Adresses qui designent le poste lui-meme.
ADRESSES_LOCALES = frozenset({'127.0.0.1', '::1', 'localhost'})

# Valeurs textuelles considerees comme "non" dans les variables d'environnement.
FAUX = frozenset({'0', 'false', 'non', 'no', 'off', '', 'desactive', 'desactivee'})


def _lire_reglage(nom, defaut='True'):
    """Lit un reglage dans les settings puis dans l'environnement."""
    valeur = getattr(settings, nom, None)
    if valeur is None:
        import os
        valeur = os.environ.get(nom, defaut)
    return valeur


def caisse_locale_active():
    """Le mode caisse locale (appels sans jeton depuis le poste) est-il actif ?

    Actif par defaut : c'est ce qui permet a la caisse de fonctionner hors-ligne
    et aux boutons PDF d'ouvrir un onglet sans jeton. Peut etre desactive par la
    variable d'environnement NEXORA_CAISSE_LOCALE=False, auquel cas TOUT appel
    anonyme est refuse.
    """
    valeur = _lire_reglage('NEXORA_CAISSE_LOCALE')
    if isinstance(valeur, bool):
        return valeur
    return str(valeur).strip().lower() not in FAUX


def adresse_client(request):
    """Adresse IP du client telle que vue par le serveur (en-tete non fiable exclu)."""
    return (request.META.get('REMOTE_ADDR') or '').strip()


def _adresses_relayees(request):
    """Valeurs de X-Forwarded-For, dans l'ordre fourni (poste distant -> poste local)."""
    brut = request.META.get('HTTP_X_FORWARDED_FOR') or ''
    return [morceau.strip() for morceau in brut.split(',') if morceau.strip()]


def est_client_local(request):
    """Vrai si - et seulement si - la requete vient bien du poste lui-meme.

    Deux conditions :
    1. REMOTE_ADDR est une adresse locale (127.0.0.1 / ::1) ;
    2. aucune adresse NON locale n'apparait dans X-Forwarded-For, l'en-tete que
       pose le relais Next.js (npm run dev) lorsqu'il transmet une requete.

    Un appelant distant ne peut donc pas se faire passer pour le poste : au pire
    il se declare lui-meme distant, ce qui est PLUS strict. Un en-tete illisible
    est traite comme distant (on ne fait pas confiance a ce qu'on ne comprend pas).
    """
    adresse = adresse_client(request)
    if adresse not in ADRESSES_LOCALES:
        return False

    for relayee in _adresses_relayees(request):
        if relayee in ADRESSES_LOCALES:
            continue
        logger.info("Appel transmis par le relais pour un poste distant (%s) : traite comme distant.", relayee)
        return False

    return True
