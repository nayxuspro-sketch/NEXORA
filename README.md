# NEXORA ERP & POS — version complète corrigée

Cette archive source réunit le code fourni depuis `C:\NEXORA` et les correctifs déjà présents dans cette copie, avec le correctif v2 du bilan PDF vendeur intégré. Le ZIP complet prêt à télécharger est [`NEXORA-COMPLET-SOURCE-2026-10-08.zip`](telechargements/NEXORA-COMPLET-SOURCE-2026-10-08.zip) ; la page [Téléchargements](telechargements/index.html) le présente avec les correctifs séparés.

Consultez [`SOURCE-MANIFEST.txt`](SOURCE-MANIFEST.txt) pour la provenance, le détail des validations et les exclusions de l’archive.

## Installer sur Windows

Consultez [`INSTALLATION-COMPLETE-NEXORA.md`](INSTALLATION-COMPLETE-NEXORA.md) pour les prérequis, la préparation de l’environnement, les migrations SQLite et le démarrage backend/frontend. Cette archive est un paquet source, pas un installateur `.exe`/`.msi`.

## Contenu

- `apps/`, `config/`, `manage.py` : backend Django et API.
- `frontend/` : interface Next.js.
- `tests/` et migrations Django.
- Guides de déploiement, sécurité, base de données, stocks et rapports.

Aucune base de données, sauvegarde, identifiant ni secret de production ou configuration `.env` n’est incluse. Une installation neuve démarre avec une base vide.

## Recette réalisée sur cette copie

Le 8 octobre 2026 : `manage.py check` sans erreur ; **118 tests Django réussis, 1 ignoré** ; compilation de production Next.js réussie. Ces contrôles utilisent une base de test temporaire et ne valident pas les données de production ni les particularités d’un autre poste.

## Prototype complémentaire des permissions françaises

Le dépôt conserve également le prototype UI et le correctif Django de traduction des permissions livrés dans cette PR. Le guide dédié est [`DROITS-ET-PERMISSIONS-FR.md`](DROITS-ET-PERMISSIONS-FR.md) ; le prototype se lance sur le port 8000. Il est distinct de l’application complète Django/Next.js, qui utilise les instructions du guide d’installation ci-dessus.
