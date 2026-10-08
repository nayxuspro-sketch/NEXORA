# NEXORA — évaluation technique

**Note globale : 7.2/10 — soit 72 %** (moyenne pondérée de 7 axes)

Deux lectures : **8,0/10 en couverture métier**, et, depuis les correctifs du 8 octobre 2026, **6,8/10 en sécurité** et **6,8/10 en fiabilité**.
L'application est maintenant saine sur un poste unique ou en réseau local. Objectif suivant réaliste : **8,5/10** (HTTPS, intégration continue, découpage des écrans).

## Détail par axe

| Axe | Poids | Note | Justification |
|---|---|---|---|
| Architecture & modèle de données | 20 % | 7.5/10 | 13 applications Django, 44 modèles, héritage `TenantModel` + `TenantModelViewSet`, clés étrangères explicites, `DecimalField` partout pour l'argent, migrations régulières (29 fichiers), `on_delete` réfléchi (SET_NULL sur l'utilisateur, CASCADE sur les lignes de vente). Faiblesse : le multi-tenant est conçu mais pas imposé (voir Sécurité). |
| Couverture métier | 10 % | 8.0/10 | Vente, encaissement, caisses, retours, stock, achats, partenaires, BI, audit, PDF (rapports, étiquettes, bons, bilans), assistant IA, licences, notifications : le périmètre d'un vrai ERP de commerce. Les écrans correspondent à des besoins réels du terrain, pas à une maquette. |
| Qualité du code backend | 15 % | 7.5/10 | Conventions DRF respectées (serializers, viewsets, pagination 20, filtres, tri, OpenAPI via drf-spectacular), 13 `transaction.atomic`, 39 `select_related/prefetch_related`, gestionnaire d'exceptions centralisé, middleware d'audit, endpoint `/health/`. À corriger : 10 `except` nus, fichiers-fonctions très longs (`inventory/pdf_export.py` : 797 lignes), logique métier parfois dupliquée entre les PDF et les vues. **Corrigé le 8/10/2026 :** plus d'article, de magasin, de caisse ni de client substitué en silence dans une vente ; le remboursement d'un retour se calcule désormais au prix réellement payé (il utilisait le tarif du jour) ; les 33 défauts « flottants » des champs de montant sont corrigés (aucune migration, aucune donnée touchée) ; le rapport « état de vente individuel du vendeur » respecte désormais la période demandée (elle était écrasée par « maintenant + 4 h ») ; l'annulation d'une vente encaissée rembourse désormais l'encaissement (contre-mouvement, caisse, créance client, statut « Remboursé ») avec quatre garde-fous — 110 tests verts dans l'arbre de recette. |
| Frontend & UX | 15 % | 6.8/10 | Pile moderne et cohérente : Next.js 14 (App Router), React 18, TypeScript `strict`, Tailwind, React Query, react-hook-form + zod, scan de codes-barres, 12 écrans. À corriger : 3 pages géantes (`inventory` 1 869 lignes, `settings` 1 707, `pos` 1 332) difficiles à faire évoluer, 78 `any`, peu d'états de chargement/erreur normalisés. |
| Sécurité & permissions | 20 % | 6.8/10 | Point le plus faible, et de loin. Les permissions sont décoratives : `IsAuthenticatedAndInTenant` et `RolePermission` renvoient `True` sans condition ; 14 vues sont en `AllowAny` ; un JWT invalide est silencieusement ignoré (l'appelant devient anonyme) ; `ALLOWED_HOSTS=['*']`, CORS toutes origines avec credentials, `X-Frame-Options: ALLOWALL`, clé secrète de repli en dur, `DEBUG` à `True` par défaut, aucun throttling. Une requête anonyme retombe sur `Company.objects.first()` : elle lit donc les données de la première entreprise — et peut même en créer une. Tolérable en caisse hors-ligne isolée ; inacceptable dès que l'application est sur un réseau. **CORRIGÉ le 8 octobre 2026** : accès anonymes distants refusés sur toute l'API, rôles appliqués, CORS fermé, connexion limitée, pages de diagnostic masquées à distance (reste hors périmètre : HTTPS). |
| Tests & fiabilité | 15 % | 6.8/10 | 7 fichiers, 633 lignes de tests pour ~7 400 lignes de code métier : aucun test à l'intérieur des 13 applications, pas de couverture mesurée, pas d'intégration continue. C'est exactement pour cela qu'un bug silencieux a pu vivre longtemps dans le bilan vendeur : `if seller_param and seller_user` — une règle comptable fausse, sans aucun test pour la contredire. Les 14 tests que nous venons d'écrire montrent le chemin. **Mesuré chez vous le 8 octobre 2026** : 96 tests exécutés, tous verts (2 ignorés), dont 16 sur les règles d'argent (montants, TVA, remises, paiements, retours, clôture de caisse) ; 110 tests verts dans l'arbre de recette (5 sur les montants décimaux, 4 sur l'état de vente du vendeur, 9 sur le remboursement à l'annulation). Restent : intégration continue et couverture mesurée. |
| Exploitation, doc, déploiement | 5 % | 6.5/10 | Dockerfile (gunicorn, healthcheck), docker-compose PostgreSQL 16 + Redis, scripts de sauvegarde/restauration, scripts Windows de démarrage et de mise à jour, 32 documents Markdown. Mais : documents courts (64 lignes en moyenne), dépendances non figées (`>=`), pas de `.env` imposé, pas de CI/CD. |
| **Moyenne pondérée** |  | **7.2/10** | **72 %** |

## Ce qui est solide

- Périmètre fonctionnel réel : 13 applications, 44 modèles, 25 viewsets, 23 routes API — un ERP de commerce complet, pas une démo.
- Modèle de données propre : montants en `DecimalField`, statuts en `TextChoices`, suppressions réfléchies, traçabilité (audit, sessions de caisse, retours).
- Pile frontend moderne et cohérente : TypeScript strict, React Query, validation zod, scan de codes-barres, 12 écrans opérationnels.
- Conventions DRF sérieuses : pagination, filtres, tri, OpenAPI, gestion d'erreurs centralisée, transactions explicites.
- Cycle de vie outillé : Docker, sauvegardes, scripts d'installation/mise à jour, guides utilisateur et générateur de captures.
- Fonctions avancées présentes : BI, rapports PDF, suggestions de stock, assistant IA, licences par magasin.

## Ce qui plombe la note

- Permissions ouvertes : `IsAuthenticatedAndInTenant` et `RolePermission` renvoient toujours `True`, 14 vues en `AllowAny`, aucun throttling.
- Jeton invalide ignoré en silence (au lieu d'un 401) : une session expirée se transforme en appel anonyme, donc en accès à la première entreprise.
- Repli sur la première entreprise (`Company.objects.first()`, et création si la table est vide) dans la classe de base de toutes les vues.
- Réglages de production absents : `ALLOWED_HOSTS=['*']`, CORS ouvert avec credentials, `X-Frame-Options: ALLOWALL`, clé secrète de repli dans le code, `DEBUG` par défaut.
- Le frontend simule un succès : si le backend ne répond pas, un POST renvoie un faux objet « créé » au lieu d'échouer — dangereux en caisse, on croit avoir encaissé.
- Tests très insuffisants (633 lignes, 0 test dans les applications), aucune CI : les régressions comptables ne sont pas détectées.
- Fichiers monolithiques : trois écrans de 1 300 à 1 900 lignes et plusieurs exports PDF de 400 à 800 lignes.
- Dépendances non figées et documentation plus large que profonde : une remise en état un an plus tard sera hasardeuse.

## La faille à comprendre en une phrase

Dans `apps/common/viewsets.py`, quand l'utilisateur n'est pas identifié, la classe de base ne refuse pas la requête : elle prend `Company.objects.first()` (et la crée si la table est vide). Comme `apps/common/permissions.py` répond `True` dans tous les cas et que `OptionalJWTAuthentication` transforme un jeton invalide en appel anonyme, une simple requête sans jeton peut lire les ventes, produits et clients de la première entreprise. En poste unique hors-ligne, ça passe ; dès qu'il y a un réseau, il faut fermer.

## Plan pour passer de 59 % à 82 %

| Priorité / charge | Action |
|---|---|
| P0 — 1 à 2 jours | Fermer les accès : permissions réelles par rôle, refus anonyme (401) hors caisse locale, une entreprise déduite de l'utilisateur seulement, `ALLOWED_HOSTS` et CORS limités, `DEBUG=False` par défaut, clé secrète obligatoire au démarrage, throttling sur la connexion. Gain : +2,0 sur la note sécurité. |
| P0 — 2 heures | Supprimer la simulation de succès côté frontend : une panne du backend doit afficher une erreur, jamais un faux enregistrement. |
| P1 — 1 semaine | Tests des règles qui touchent l'argent : totaux de vente, TVA et remises, retours, stock, clôture de caisse, bilans par vendeur et par période — puis intégration continue qui les exécute à chaque envoi. |
| P2 — 1 semaine | Découper les trois écrans géants en composants, supprimer les `any`, normaliser chargement/erreurs/vides, ajouter un journal d'erreurs côté interface. |
| P3 — 2 jours | Figer les dépendances (`requirements.txt` + `package-lock.json`), imposer un `.env`, ajouter lint/format automatiques et une procédure de restauration testée. |

## Ce que cette note ne dit pas

Elle ne juge pas votre exploitation réelle : une application suffisamment complète vivante sur un poste vaut mieux qu'un squelette parfait. Elle ne dit pas non plus que les fonctions métier sont fausses — au contraire, la campagne de tests menée aujourd'hui sur le bilan vendeur (14/14) montre que les règles d'encaissement tiennent quand on les vérifie. Le déficit est dans *la preuve* : permissions non appliquées, règles d'argent non testées, aucune intégration continue pour empêcher un retour en arrière.

---
Mesures : 120 fichiers Python (8 338 lignes, dont 7 406 hors migrations), 36 fichiers TypeScript (10 695 lignes), 44 modèles, 38 serializers, 25 viewsets, 23 routes, 29 migrations, 96 tests verts le 8/10/2026 sur le poste de production, 32 documents Markdown (2 053 lignes), 0 fichier de CI. Aucun secret reproduit.