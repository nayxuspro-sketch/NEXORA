# Plan d'améliorations — NEXORA (post-audit)

Objectif : exploitation fiable en magasin, **30 utilisateurs simultanés**.
Références : audit technique (sections [1] à [4]) + chantiers réalisés
(permissions FR, dispositions PDF, serveurs).

Légende effort : S = < 2 h, M = 0,5 j, L = 1 j ou plus.

---

## P0 — Bloquants avant l'ouverture en magasin

- [ ] **[1] PostgreSQL à la place de SQLite** (M→L)
  Pourquoi : écritures sérialisées -> « database is locked » dès 10-15 postes.
  Comment : installer PostgreSQL 16, `dumpdata` -> `loaddata` (ou pgloader si déjà PG-compatible),
  `DATABASES` dans settings, `CONN_MAX_AGE = 60`.
- [ ] **[1] Serveurs de production des deux côtés** (M)
  Pourquoi : `next dev` et `runserver` observés = non robustes, mono-processus.
  Comment : `pip install waitress` puis `waitress-serve --threads=8 --port=8000 config.wsgi:application` ;
  front : `npm run build` + `npm run start` ; les deux en **services Windows** (nssm) avec redémarrage auto.
- [ ] **[3] Fermer la configuration de production** (S)
  `DEBUG = False`, `ALLOWED_HOSTS` = domaine interne uniquement,
  `CORS_ALLOWED_ORIGINS` = origine du front uniquement, `SECRET_KEY` via variable d'environnement.
- [ ] **[4] Sauvegardes automatisées + test de restauration** (M)
  pg_dump quotidien + copie NAS/externe + restauration testée trimestriellement ;
  conserver 14 générations.
- [ ] **[3] TLS interne + cookies sécurisés** (M)
  Caddy ou nginx en reverse proxy (certificat interne LAN) ;
  `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_PROXY_SSL_HEADER`.

## P1 — Majeurs (premier mois d'exploitation)

- [x] **[2] Courses concurrentes sur les parcours ventes/achats** (chantier ① terminé)
  `sales/services.py` et `purchases/services.py` corrigés avec `select_for_update()` ;
  `inventory/services.py` était déjà verrouillé et `inventory/views.py` délègue au service.
  Vérifié par l'audit du 05/10/2026 à 15:19 : ventes et achats affichés `[OK]`.
  **À part** : `ai_assistant/automation.py` reste `[ATTENTION]` dans le scan statique ;
  vérifier séparément son périmètre si cette automatisation touche au stock ou à la caisse.
- [ ] **Tests automatisés des parcours critiques** (L)
  Ticket de caisse, décrément de stock, retour vente, ouverture/clôture de session,
  contrôle des permissions par profil. `py manage.py test` dans la CI (ou script pré-commit).
- [ ] **[3] Durcissement JWT** (S)
  `ROTATE_REFRESH_TOKENS = True`, app `rest_framework_simplejwt.token_blacklist`,
  durées de vie courtes (access 30 min, refresh 8 h).
- [ ] **Exports PDF asynchrones ou bridés** (M)
  File (Celery + Redis) ou au minimum limite de concurrence + cache du catalogue
  par statut pendant 5 min ; sinon risque de saturation des workers à 30 postes.
- [ ] **Journalisation & supervision** (M)
  `LOGGING` avec fichiers rotatifs (Django + Next via service) ; alerte sur erreurs 500 ;
  watchdog redémarrant waitress/Next en cas de crash.
- [ ] **Performance des listes & rapports** (M)
  `select_related`/`prefetch_related` sur les endpoints de tickets, stocks et rapports ;
  index sur les champs de date et clés étrangères filtrées ; pagination systématique.

## P2 — Moyens (trimestre)

- [ ] **[3] Whitenoise** pour servir `/static` et `/media` côté Django en production (S).
- [ ] **HSTS** (`SECURE_HSTS_SECONDS = 31536000`) une fois TLS stabilisé (S).
- [ ] **Moindre privilège RBAC** : retirer « Peut supprimer » des profils caisse/vente ;
  séparation des tâches paiement vs rapprochement (règles déjà documentées) (S).
- [ ] **Contrôles d'intégrité quotidiens** (M) : stock négatif, session non équilibrée,
  trou de numérotation de ticket -> notification Direction (app `notifications` existante).
- [ ] **Mode dégradé caisse** (L, roadmap produit) : file locale des tickets si coupure
  réseau, synchronisation au retour — indispensable en retail.
- [ ] **i18n pérenne** : `LANGUAGE_CODE = "fr-fr"` ; le signal `post_migrate` fourni
  traduit déjà les nouvelles permissions (S).
- [ ] **Documentation d'exploitation** (M) : runbook redémarrage, sauvegarde, restauration,
  retour arrière de migration, contacts d'astreinte.
- [ ] **Test de charge 30 clients** (M) : script Locust sur `/api/v1/pos/` et `/api/v1/sales/`
  avant ouverture ; cible p95 < 300 ms.

## P3 — Mineurs / dette technique

- [ ] `verbose_name` français restants : `store license`, `purchase return item`,
  `sale return item` (Meta des modèles) puis relancer `traduire_permissions` (S).
- [ ] Nettoyage des HTML statiques racine (`download.html`, guides) : les servir via
  le front ou les archiver (S).
- [ ] Synchronisation NTP de tous les postes du magasin (horodatage tickets/audit) (S).
- [ ] Exposition interne du schéma OpenAPI (`drf-spectacular`) pour les intégrations futures (S).
- [ ] Archivage numéroté des PDF générés (piste d'audit documentaire) (M).

---

## Charge estimée

| Lot | Effort |
| --- | --- |
| P0 (ouverture) | 3 à 4 jours-homme |
| P1 (mois 1) | 4 à 5 jours-homme |
| P2 (trimestre) | 6 à 8 jours-homme |
| P3 (fil de l'eau) | 1 à 2 jours-homme |

## Outil de suivi

Relancer `py manage.py audit_production` après chaque lot : les tags
`[CRITIQUE]` doivent disparaître section par section (P0 -> [1][3][4],
P1 -> [2], etc.). Le rapport `.txt` horodaté sert de preuve d'état à chaque jalon.

---

## Constats réels — audit du 05/10/2026 (`audit_production_20261005_131845.txt`)

| # | Constat | Valeur relevée | Impact sur le plan |
|---|---|---|---|
| 1 | Moteur de base | **SQLite** (`D:\NEXORA\db.sqlite3`, 844 Ko, `CONN_MAX_AGE=0`) | P0-1 confirmé — migration facile (base quasi vide) |
| 2 | Transactions | `pos/views.py`, `inventory/views.py`, `reports/views.py`, `ai_assistant/service.py` **sans atomic** ; `sales/services.py`, `purchases/services.py`, `ai_assistant/automation.py` **atomic sans select_for_update** ; `inventory/services.py` OK | P1-6 **remonté en tête** : 6 fichiers à corriger avant toute vente réelle |
| 3 | Config | `DEBUG=True` 🔴, `ALLOWED_HOSTS=['*']`, **CORS toutes origines** 🔴 ; SECRET_KEY via env ✅, JWT rotation ✅ ; blacklist, whitenoise, LOGGING, cookies sécurisés absents | P0-3 confirmé ; P2-12/13 et P1-8 à faire |
| 4 | Sauvegardes | **0 trouvée** 🔴 ; volumes 7 j = 0 partout, 3 utilisateurs actifs | P0-4 confirmé ; le système n'est pas encore exploité → durcir MAINTENANT, sans données à risque |

**Note** : la ligne `audit_production.py [OK]` de la section [2] est un faux positif (le scanner détecte les mots-clés dans son propre code source) — à ignorer.

**Ordre d'exécution réactualisé** : ① transactions ventes/achats — terminé → ② PostgreSQL → ③ config production (DEBUG/CORS/hosts + whitenoise + LOGGING) → ④ sauvegardes + serveurs en service Windows → ⑤ TLS + cookies sécurisés → ⑥ JWT blacklist.

## Mise à jour — audit après chantier ① (05/10/2026, 15:19)

- `apps/sales/services.py` et `apps/purchases/services.py` sont désormais `[OK] atomic + select_for_update` ; `py manage.py check` ne signale aucune erreur.
- `apps/inventory/services.py` est `[OK]` ; l'alerte sur `inventory/views.py` est un faux positif confirmé (la vue délègue à ce service). Les alertes de `pos/views.py`, `reports/views.py` et `ai_assistant/service.py` ne correspondent pas à des écritures concurrentes de stock dans les parcours analysés (sessions de caisse sans mouvement de stock, rapports/assistant en lecture seule).
- `apps/ai_assistant/automation.py` reste `[ATTENTION] atomic sans select_for_update` : à examiner séparément si cette automatisation modifie réellement le stock ou la caisse.
- **Prochain chantier : PostgreSQL.** L'application utilise toujours SQLite ; ses verrous `select_for_update()` ne protègent donc pas des accès concurrents tant que le moteur n'a pas été migré.
- Diagnostic sans modification préparé : `telechargements/diagnostic_postgresql.ps1`. Il relève la version Django/pilote, le fichier settings actif, l'état local de PostgreSQL et les migrations ; mots de passe et `SECRET_KEY` ne sont pas affichés.
- 05/10/2026 : copie SQLite pré-migration créée (`D:\NEXORA\db.sqlite3.pre-postgresql-20261005_155943.bak`, 864256 octets), `PRAGMA integrity_check=ok`. C'est un instantané ponctuel, pas encore une stratégie de sauvegarde automatisée.
- Récupération du compte administrateur PostgreSQL préparée : `telechargements/reinitialiser_acces_postgresql.ps1` ajoute temporairement une règle `trust` strictement locale, change le mot de passe avec l'invite masquée, puis restaure `pg_hba.conf` et redémarre le service.
