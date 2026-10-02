# -*- coding: utf-8 -*-
"""
Traduction française des libellés de permissions de la fenêtre
« Configurer les Droits : Direction & Administration Générale ».

Problème constaté dans l'application : les cases de la grille affichent
« Can add Utilisateur », « Can change Règle d'Automatisation », etc.
Ces préfixes anglais sont les noms de permissions par défaut de Django
(``Can add %s``, ``Can change %s``, ``Can delete %s``, ``Can view %s``),
enregistrés en base dans la langue active au moment de ``migrate``
(souvent l'anglais), alors que les noms de modèles sont déjà en français.

Ce module fournit trois moyens de tout passer en français :

1. ``VERBES_FR`` / ``traduire_nom_permission`` — correspondance et fonction
   de traduction réutilisable (templates, API REST, JavaScript…).
2. ``filtrer_permission_fr`` — filtre de template Django :
   ``{{ permission|permission_fr }}`` affiche « Peut ajouter Utilisateur ».
3. ``traduire_permissions_post_migrate`` — signal ``post_migrate`` qui
   traduit automatiquement les permissions dès leur création.

Et, pour corriger l'existant sans redéployer de code d'affichage, la
commande de gestion ``traduire_permissions`` (voir
``management/commands/traduire_permissions.py``) qui renomme en base les
``Permission.name`` déjà créées.

Installation rapide
-------------------
1. Copier le paquet ``integration_django`` dans une app Django existante
   (par ex. ``profils/integration_django/``), ou ajouter ce fichier tel quel ;
2. Enregistrer le signal dans le ``AppConfig.ready()`` de l'app :

       from django.apps import AppConfig

       class ProfilsConfig(AppConfig):
           name = "profils"

           def ready(self):
               from .integration_django.permissions_fr import (
                   traduire_permissions_post_migrate,
               )
               from django.db.models.signals import post_migrate
               post_migrate.connect(traduire_permissions_post_migrate, sender=self)

3. Lancer une fois : ``python manage.py traduire_permissions``.
"""

from django import template
from django.db.models.signals import post_migrate

register = template.Library()

#: Correspondance anglais -> français des préfixes de permissions Django.
#: « view » est rendu par « Peut consulter » (plus lisible en contexte
#: métier que le « Peut voir » du catalogue Django) ; remplacer librement.
VERBES_FR = {
    "Can add": "Peut ajouter",
    "Can change": "Peut modifier",
    "Can delete": "Peut supprimer",
    "Can view": "Peut consulter",
}

#: Ordre d'affichage des verbes dans la grille (cf. capture d'écran).
ORDRE_VERBES = ("add", "change", "delete", "view")

#: Libellé d'un verbe seul, pour construire la grille côté interface.
VERBES_SEULS_FR = {
    "add": "Peut ajouter",
    "change": "Peut modifier",
    "delete": "Peut supprimer",
    "view": "Peut consulter",
}


def traduire_nom_permission(nom):
    """Traduit un nom de permission Django stocké en anglais.

    >>> traduire_nom_permission("Can add Utilisateur")
    'Peut ajouter Utilisateur'
    >>> traduire_nom_permission("Can view Règle d'Automatisation")
    'Peut consulter Règle d'Automatisation'
    >>> traduire_nom_permission("Peut modifier Utilisateur")
    'Peut modifier Utilisateur'
    """
    for anglais, francais in VERBES_FR.items():
        prefixe = anglais + " "
        if nom.startswith(prefixe):
            return francais + nom[len(prefixe):]
    return nom


@register.filter("permission_fr")
def filtrer_permission_fr(permission):
    """Filtre de template : ``{{ permission|permission_fr }}``."""
    nom = getattr(permission, "name", permission)
    return traduire_nom_permission(str(nom))


def traduire_permissions_post_migrate(sender, apps=None, **kwargs):
    """Signal ``post_migrate`` : traduit les permissions nouvellement créées.

    À connecter dans ``AppConfig.ready()`` (voir docstring du module).
    """
    if apps is None:
        return
    try:
        Permission = apps.get_model("auth", "Permission")
    except LookupError:
        return
    a_modifier = []
    for permission in Permission.objects.all():
        nouveau = traduire_nom_permission(permission.name)
        if nouveau != permission.name:
            permission.name = nouveau
            a_modifier.append(permission)
    if a_modifier:
        Permission.objects.bulk_update(a_modifier, ["name"])
