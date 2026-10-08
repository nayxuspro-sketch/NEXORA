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
        a_modifier = []
        for permission in Permission.objects.all().order_by("content_type__app_label", "codename"):
            nom = permission.name
            for ancien, nouveau in table.items():
                prefixe = ancien + " "
                if nom.startswith(prefixe):
                    permission.name = nouveau + " " + nom[len(prefixe):]
                    a_modifier.append(permission)
                    self.stdout.write(
                        "%s.%s : %s -> %s"
                        % (permission.content_type.app_label, permission.codename, nom, permission.name)
                    )
                    break
        if not a_modifier:
            self.stdout.write(self.style.SUCCESS("Aucun nom de permission à traduire."))
            return
        if options["dry_run"]:
            self.stdout.write(self.style.WARNING("%d renommage(s) simulé(s) (--dry-run)." % len(a_modifier)))
            return
        Permission.objects.bulk_update(a_modifier, ["name"])
        self.stdout.write(self.style.SUCCESS("%d nom(s) de permission traduit(s)." % len(a_modifier)))
