# NEXORA - Modélisation des Menaces (Threat Model - STRIDE)

Le modèle de menaces de NEXORA est structuré selon la méthodologie reconnue **STRIDE** (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege).

---

## 1. Cartographie des Risques STRIDE & Contre-Mesures

### 1. Spoofing (Usurpation d'Identité)
- **Menace** : Vol ou falsification d'un jeton d'authentification ou force brute sur les mots de passe.
- **Contre-Mesures NEXORA** :
  - Hachage cryptographique fort des mots de passe (PBKDF2 SHA-256 avec sel aléatoire).
  - Jetons JWT signés cryptographiquement (`SimpleJWT`), expiration courte de l'access token (60 min) et rotation sécurisée du refresh token.
  - Journalisation de l'adresse IP à chaque connexion.

### 2. Tampering (Altération des Données)
- **Menace** : Falsification d'un prix de vente, injection de stocks frauduleux ou modification de statuts de caisse.
- **Contre-Mesures NEXORA** :
  - Calculs financiers centralisés dans les **Domain Services** côté serveur (`SaleService`, `StockService`) ; le client frontend ne peut imposer un calcul financier arbitraire.
  - Transactions SQL atomiques (`@transaction.atomic`) avec verrouillage pessimiste (`select_for_update()`).

### 3. Repudiation (Répudiation d'une Action)
- **Menace** : Un caissier ou gestionnaire nie avoir effectué une annulation de vente ou une régularisation de stock négative.
- **Contre-Mesures NEXORA** :
  - Table immuable `StockMovement` horodatant chaque unité sortie avec référence utilisateur (`user_id`).
  - Table immuable `AuditLog` enregistrant les actions mutantes et l'adresse IP source.

### 4. Information Disclosure (Fuite d'Informations & Multi-Tenant)
- **Menace** : Une entreprise cliente A accède aux commandes ou à la marge d'une entreprise concurrente B (IDOR).
- **Contre-Mesures NEXORA** :
  - Héritage systématique de `TenantModel` avec clé étrangère non nulle `company_id`.
  - Filtrage obligatoire au niveau du QuerySet DRF (`TenantModelViewSet.get_queryset()`).
  - Renvoi d'une erreur `404 Not Found` en cas de tentative d'accès direct par UUID afin de masquer jusqu'à l'existence de l'entité.

### 5. Denial of Service (Déni de Service)
- **Menace** : Requêtes massives dégradant la base de données.
- **Contre-Mesures NEXORA** :
  - Pagination obligatoire (`StandardResultsSetPagination`) bornant le nombre maximal d'enregistrements retournés à 200 par page.
  - Indexation en base sur les clés primaires, colonnes de recherche (`sku`, `barcode`, `name`) et clés de partitionnement `company_id`.

### 6. Elevation of Privilege (Élévation de Privilèges)
- **Menace** : Un employé (vendeur/caissier) modifie son rôle pour accéder au dashboard de direction ou aux marges.
- **Contre-Mesures NEXORA** :
  - Vérification explicite du rôle dans `perform_update` : seul un `ADMIN` peut changer un rôle.
  - Contrôle d'accès RBAC au niveau des endpoints sensibles de l'API et de l'assistant IA.
