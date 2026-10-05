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

- [ ] **[2] Transactions de stock atomiques avec verrouillage** (L)
  Tout décrément `StockLevel` / création `StockMovement` / ticket `Sale` dans
  `transaction.atomic()` + `select_for_update()` ; idem clôture de session de caisse.
  Vérifié par : section [2] de `py manage.py audit_production`.
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

**Ordre d'exécution réactualisé** : ① transactions stock (6 fichiers) → ② PostgreSQL → ③ config production (DEBUG/CORS/hosts + whitenoise + LOGGING) → ④ sauvegardes + serveurs en service Windows → ⑤ TLS + cookies sécurisés → ⑥ JWT blacklist.
