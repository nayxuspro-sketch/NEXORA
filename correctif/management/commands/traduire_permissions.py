# -*- coding: utf-8 -*-
"""
Commande de gestion : ``python manage.py traduire_permissions``

À placer OBLIGATOIREMENT dans ``<app>/management/commands/`` (racine de
l'app), car Django ne recherche les commandes de gestion que dans ce
dossier précis — pas dans un sous-paquet comme ``integration_django/``.

Renomme en base de données les ``Permission.name`` créés en anglais
(« Can add … », « Can change … », « Can delete … », « Can view … ») vers
leurs équivalents français (« Peut ajouter … », « Peut modifier … »,
« Peut supprimer … », « Peut consulter … »), sans toucher aux codes
(``codename``) utilisés par ``has_perm``.

Fichier volontairement autonome (aucun import du paquet
``integration_django``) pour fonctionner quel que soit l'endroit où le
dossier ``management/`` est collé.

Usage :
    python manage.py traduire_permissions            # applique
    python manage.py traduire_permissions --dry-run  # simule
    python manage.py traduire_permissions --revert   # revient à l'anglais
"""

from django.contrib.auth.models import Permission
from django.core.management.base import BaseCommand

#: Même table que dans ``integration_django/permissions_fr.py``.
VERBES_FR = {
    "Can add": "Peut ajouter",
    "Can change": "Peut modifier",
    "Can delete": "Peut supprimer",
    "Can view": "Peut consulter",
}

VERBES_EN = {fr: en for en, fr in VERBES_FR.items()}

#: Noms de modèles laissés en anglais par Django (modèles internes ou sans
#: ``verbose_name``). Appliqués en suffixe du libellé, après le verbe.
NOMS_MODELES_FR = {
    "log entry": "Entrée de journal",
    "group": "Groupe",
    "permission": "Permission",
    "content type": "Type de contenu",
    "session": "Session",
    "store license": "Licence de magasin",
    "purchase return item": "Ligne de retour fournisseur",
    "sale return item": "Ligne de retour vente",
}

NOMS_MODELES_EN = {fr: en for en, fr in NOMS_MODELES_FR.items()}


class Command(BaseCommand):
    help = (
        "Traduit en français les noms de permissions Django stockés en anglais "
        "(« Can add … » → « Peut ajouter … »), tels qu'affichés dans la fenêtre "
        "« Configurer les Droits : Direction & Administration Générale »."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Affiche les renommages sans les écrire en base.",
        )
        parser.add_argument(
            "--revert",
            action="store_true",
            help="Opération inverse : français → anglais.",
        )

    def handle(self, *args, **options):
        table = VERBES_EN if options["revert"] else VERBES_FR
        modeles = NOMS_MODELES_EN if options["revert"] else NOMS_MODELES_FR
        a_modifier = []
        for permission in Permission.objects.all().order_by("content_type__app_label", "codename"):
            nom = permission.name
            nouveau_nom = nom
            for ancien, nouveau in table.items():
                prefixe = ancien + " "
                if nouveau_nom.startswith(prefixe):
                    nouveau_nom = nouveau + " " + nouveau_nom[len(prefixe):]
                    break
            for ancien, nouveau in modeles.items():
                suffixe = " " + ancien
                if nouveau_nom.endswith(suffixe):
                    nouveau_nom = nouveau_nom[: -len(suffixe)] + " " + nouveau
                    break
            if nouveau_nom != nom:
                permission.name = nouveau_nom
                a_modifier.append(permission)
                self.stdout.write(
                    "%s.%s : %s -> %s"
                    % (permission.content_type.app_label, permission.codename, nom, nouveau_nom)
                )
        if not a_modifier:
            self.stdout.write(self.style.SUCCESS("Aucun nom de permission à traduire."))
            return
        if options["dry_run"]:
            self.stdout.write(self.style.WARNING("%d renommage(s) simulé(s) (--dry-run)." % len(a_modifier)))
            return
        Permission.objects.bulk_update(a_modifier, ["name"])
        self.stdout.write(self.style.SUCCESS("%d nom(s) de permission traduit(s)." % len(a_modifier)))
