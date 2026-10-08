# NEXORA - Liste de Contrôle de Sécurité (Security Checklist)

Cette checklist doit être validée à chaque cycle de déploiement et intégration continue (CI/CD).

---

## 1. Authentification & Gestion des Sessions
- [x] Les mots de passe sont hachés avec un algorithme standard robuste (PBKDF2 SHA-256 avec sel).
- [x] Politique de complexité minimale des mots de passe activée (longueur minimale 8 caractères, contrôle des similitudes).
- [x] L'authentification par API s'effectue via des jetons JWT signés et horodatés.
- [x] Les tokens d'accès ont une durée de vie limitée (60 minutes).
- [x] Déconnexion propre côté client avec purge immédiate des jetons du stockage local.

---

## 2. Cloisonnement Multi-Tenant & Autorisation
- [x] Tout modèle de données métier sensible hérite de `TenantModel` avec référence obligatoire à `company`.
- [x] Tout ViewSet hérite de `TenantModelViewSet` pour garantir un filtrage automatique sur `company_id`.
- [x] Les tentatives d'accès inter-entreprises (IDOR) renvoient systématiquement un code HTTP `404 Not Found`.
- [x] Le rôle `ADMIN` est obligatoire pour créer ou modifier un compte utilisateur au sein de l'entreprise.
- [x] Les rôles non autorisés (`CASHIER`, `STOCK_KEEPER`) ne peuvent pas consulter les indicateurs de marge financière.

---

## 3. Sécurité de la Base de Données
- [x] Requêtes paramétrées via l'ORM Django protégeant nativement contre les injections SQL.
- [x] Opérations de stock et de vente encapsulées dans des transactions atomiques (`@transaction.atomic`).
- [x] Verrouillage pessimiste de lignes (`select_for_update()`) prévenant les conditions de concurrence ("race conditions").
- [x] Contraintes d'intégrité référentielle et d'unicité respectées (`unique_together` par tenant).

---

## 4. Sécurité Frontend & API
- [x] Pagination systématique des listes pour empêcher l'épuisement mémoire et le déni de service.
- [x] Échappement automatique React protégeant contre les failles XSS.
- [x] Protection contre le détournement de clics (`XFrameOptionsMiddleware`).
- [x] En-têtes CORS configurés de façon maîtrisée.
- [x] Gestion normalisée des erreurs ne divulguant jamais de traces de pile ("stack traces") en production.

---

## 5. Journalisation d'Audit & Détection
- [x] Middleware d'audit consignant automatiquement les connexions réussies (`LOGIN_SUCCESS`).
- [x] Enregistrement immédiat de chaque tentative de contournement d'autorisation (`PERMISSION_DENIED_ATTEMPT`).
- [x] Capture de l'adresse IP et de l'utilisateur sur toutes les actions modifiant les données.
- [x] Suite de tests de sécurité automatisée intégrée (`test_security_audit.py`).
