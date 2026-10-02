# NEXORA

Plateforme Vente SAAS.

## Fenêtre « Configurer les Droits : Direction & Administration Générale » — en français

Écran de gestion des habilitations **intégralement en français (`fr-FR`)**.

### `index.html` — la fenêtre de la capture d'écran, traduite

Réplique fidèle et fonctionnelle de la fenêtre réelle (thème sombre), dont les seuls
éléments encore en anglais étaient les préfixes de permissions hérités de Django :

| Libellé d'origine (anglais) | Libellé français appliqué |
| --- | --- |
| `Can add Utilisateur` | **Peut ajouter Utilisateur** |
| `Can change Règle d'Automatisation` | **Peut modifier Règle d'Automatisation** |
| `Can delete Journal d'Exécution Règle` | **Peut supprimer Journal d'Exécution Règle** |
| `Can view …` | **Peut consulter …** |

Tout le reste y est en français : « Nom du Profil / Rôle Métier * », « Grille des Droits
d'Accès & Permissions Granulaires », « 17 sélectionnée(s) », « Tout sélectionner »,
les sections « Gestion des Utilisateurs & Équipes », « Assistant IA & Règles
d'Automatisation », « Direction & Administration Générale », ainsi que les boutons
« Annuler » et « Enregistrer le Profil et les Droits ».

### `integration_django/` — corriger l'application Django d'origine

Les libellés `Can add …` proviennent des `Permission.name` **enregistrés en base dans la
langue active au moment de `migrate`**. Le paquet `integration_django` fournit :

- `permissions_fr.py` : correspondance `VERBES_FR`, fonction `traduire_nom_permission`,
  filtre de template `{{ permission|permission_fr }}` et signal `post_migrate`
  (traduit automatiquement les permissions nouvellement créées) ;
- `management/commands/traduire_permissions.py` : commande
  `python manage.py traduire_permissions` (avec `--dry-run` et `--revert`) qui renomme
  en base les permissions existantes, sans toucher aux `codename` utilisés par `has_perm`.

Installation : copier `integration_django/` dans une app Django, connecter le signal dans
`AppConfig.ready()` (exemple dans la docstring de `permissions_fr.py`), puis lancer la
commande une fois.

### Autres fichiers

| Fichier | Rôle |
| --- | --- |
| `matrice-droits.html`, `app.js`, `donnees.js`, `styles.css` | Matrice avancée des droits (vue complémentaire : niveaux, portées, circuits de validation, profils, historique) |
| `i18n/fr-FR.json` | Toutes les chaînes des deux écrans en français, y compris la correspondance `Can add → Peut ajouter`, etc. |

### Sections et permissions couvertes par la grille

- **Gestion des Utilisateurs & Équipes** — Utilisateur
- **Assistant IA & Règles d'Automatisation** — Journal d'Exécution Règle, Règle d'Automatisation
- **Direction & Administration Générale** — Note de Service, Document Administratif

### Exécution locale

Aucune dépendance ni étape de compilation :

```bash
python3 -m http.server 8000 --bind 0.0.0.0
# puis ouvrir http://localhost:8000  (fenêtre traduite)
#          http://localhost:8000/matrice-droits.html  (matrice avancée)
```
