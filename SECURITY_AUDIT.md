# NEXORA - Audit de Sécurité et Tests d'Intrusion

## 1. Contexte & Périmètre de l'Audit

L'audit de sécurité a été mené de façon transversale sur les composants :
- **Authentification & Session** : Tokens JWT, rotation, durée de vie, hachage PBKDF2 des mots de passe.
- **Autorisation & Multi-Tenant** : Cloisonnement strict des données entre entreprises clientes (Tenants), prévention IDOR.
- **Contrôle d'Accès Basé sur les Rôles (RBAC)** : Barrières d'élévation de privilèges (`ADMIN`, `MANAGER`, `CASHIER`, `STOCK_KEEPER`).
- **Surface d'Exposition API** : Tests d'injection SQL/NoSQL, validation stricte des serializers, pagination systématique.
- **Frontend & Client Web** : Mitigation des failles XSS, politique CORS, gestion des tokens dans le navigateur.
- **Journalisation de Sécurité** : Traçabilité des connexions et des rejets de permissions.

---

## 2. Résultats des Scénarios d'Attaque Contrôlés (Penetration Tests)

| Vecteur d'Attaque Testé | Scénario Simulé | Comportement Observé | Statut |
| :--- | :--- | :--- | :---: |
| **IDOR Cross-Tenant** | Un utilisateur de l'entreprise Alpha tente de modifier un produit de l'entreprise Beta via son UUID direct. | Rejet immédiat avec `404 Not Found` (masquage de l'existence de l'objet). Aucune fuite d'information. | **BLOQUÉ** ✅ |
| **Élévation de Privilèges** | Un compte avec le rôle `CASHIER` tente de modifier son profil pour s'auto-attribuer le rôle `ADMIN`. | Rejet avec `403 Forbidden`. Le rôle en base de données demeure inchangé. | **BLOQUÉ** ✅ |
| **Création d'Utilisateur Illégitime** | Un collaborateur non-administrateur tente de créer un nouvel utilisateur dans son entreprise. | Rejet avec `403 Forbidden` (`PermissionDenied`). Seul un `ADMIN` peut administrer les comptes. | **BLOQUÉ** ✅ |
| **Injection SQL via Recherche** | Injection d'un payload SQL type `'; DROP TABLE apps_catalog_product; --` dans les paramètres de filtre. | Requête paramétrée de façon sécurisée par l'ORM Django. Table intacte, code retour `200 OK` avec résultat vide. | **SÉCURISÉ** ✅ |
| **Tentatives d'Intrusion Auditées** | Surveillance des rejets de droits d'accès. | Chaque code `403` déclenche l'écriture automatique d'un enregistrement `PERMISSION_DENIED_ATTEMPT` dans `AuditLog`. | **TRAÇABLE** ✅ |

---

## 3. Analyse des Vulnérabilités Identifiées & Correctifs Appliqués

1. **Tentative d'Élévation de Rôle dans `UserViewSet`** :
   - *Risque* : Un utilisateur modifiant son profil via PATCH pouvait théoriquement inclure `'role': 'ADMIN'`.
   - *Correctif appliqué* : Implémentation de `perform_update` et `perform_create` dans `apps/accounts/views.py` imposant que seul un utilisateur avec `role == 'ADMIN'` peut modifier les rôles ou créer de nouveaux utilisateurs.

2. **Absence de Traçabilité Systématique des Requêtes Sensibles** :
   - *Risque* : Difficulté à auditer a posteriori les modifications de données ou les tentatives d'accès interdit.
   - *Correctif appliqué* : Création du middleware `SecurityAuditLoggingMiddleware` (`apps/audit/middleware.py`) consignant automatiquement :
     - Les succès de connexion (`LOGIN_SUCCESS`).
     - Les tentatives rejetées (`PERMISSION_DENIED_ATTEMPT`).
     - Toutes les requêtes mutantes (`POST`, `PUT`, `PATCH`, `DELETE`) avec l'adresse IP et l'identité de l'opérateur.
