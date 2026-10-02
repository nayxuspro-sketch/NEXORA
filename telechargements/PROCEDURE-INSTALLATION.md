# Procédure de mise à jour — Traduction française des permissions
## Fenêtre « Configurer les Droits : Direction & Administration Générale »

Objectif : remplacer les libellés anglais hérités de Django
(`Can add …`, `Can change …`, `Can delete …`, `Can view …`)
par leurs équivalents français
(`Peut ajouter …`, `Peut modifier …`, `Peut supprimer …`, `Peut consulter …`).

Contenu de l'archive :

    integration_django/
    ├── __init__.py
    ├── permissions_fr.py                        ← table de correspondance, filtre de template, signal post_migrate
    └── management/
        ├── __init__.py
        └── commands/
            ├── __init__.py
            └── traduire_permissions.py          ← commande manage.py
    i18n/fr-FR.json                              ← chaînes françaises (dont la correspondance des verbes)
    fenetre-configurer-droits.html               ← la fenêtre traduite, pour référence visuelle

---

## Étape 0 — Précautions

- Sauvegardez la base (ou au minimum la table `auth_permission`).
- Aucune interruption de service n'est requise : seule la colonne `name`
  (libellé affiché) est modifiée. Les `codename` (`add_utilisateur`, …),
  `has_perm()`, `@permission_required`, groupes et rôles ne changent pas.

## Étape 1 — Déposer les fichiers

Copiez le dossier `integration_django/` dans une app Django existante
(exemple ci-dessous avec une app nommée `profils`) :

    profils/
    └── integration_django/
        ├── __init__.py               (vide)
        ├── permissions_fr.py
        └── management/
            ├── __init__.py           (vide)
            └── commands/
                ├── __init__.py       (vide)
                └── traduire_permissions.py

Contrainte unique : conserver les deux niveaux de paquets, car la commande
utilise l'import relatif `from ..permissions_fr import VERBES_FR`.

## Étape 2 — Brancher le signal (futures migrations traduites automatiquement)

Dans `profils/apps.py` :

    from django.apps import AppConfig


    class ProfilsConfig(AppConfig):
        name = "profils"

        def ready(self):
            from django.db.models.signals import post_migrate
            from .integration_django.permissions_fr import traduire_permissions_post_migrate
            post_migrate.connect(traduire_permissions_post_migrate, sender=self)

## Étape 3 — Simuler

    python manage.py traduire_permissions --dry-run

Sortie attendue (extraits) :

    accounts.utilisateur : Can add Utilisateur -> Peut ajouter Utilisateur
    automatisation.regledautomatisation : Can view Règle d'Automatisation -> Peut consulter Règle d'Automatisation
    N renommage(s) simulé(s) (--dry-run).

## Étape 4 — Appliquer puis redémarrer

    python manage.py traduire_permissions
    # redémarrer gunicorn / uwsgi / runserver

## Étape 5 — Vérifier

    python manage.py shell -c "from django.contrib.auth.models import Permission; print([p.name for p in Permission.objects.filter(codename__startswith='add_')][:5])"

→ doit afficher `['Peut ajouter …', …]`. Ouvrir ensuite la fenêtre
« Configurer les Droits » : les cases sont en français.

## Étape 6 — Cas particuliers

- Templates affichant `{{ permission.name }}` : après l'étape 4 la base est
  déjà traduite ; sinon, sans toucher à la base :

      {% load permissions_fr %}
      <label>{{ permission|permission_fr }}</label>

- Front JavaScript qui reconstruit les libellés depuis les `codename` :
  utiliser `i18n/fr-FR.json` (clef `permissions`) ou `VERBES_SEULS_FR`.
- Recommandation : `LANGUAGE_CODE = "fr-fr"` dans `settings.py`.

## Étape 7 — Retour arrière

    python manage.py traduire_permissions --revert

---

Garanties : opération idempotente, réversible, testable à blanc, sans effet
sur les autorisations, et pérenne (signal `post_migrate`).
