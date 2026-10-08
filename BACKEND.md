# NEXORA - Documentation Backend

## 1. Vue d'ensemble de l'Architecture

NEXORA est un progiciel de gestion intégré (ERP) et système de point de vente moderne pour entreprises commerciales, structuré autour du cycle de valeur :
$$\text{Vente} \longrightarrow \text{Gestion} \longrightarrow \text{Compréhension} \longrightarrow \text{Anticipation} \longrightarrow \text{Automatisation}$$

### Technologies Clés
- **Langage** : Python 3.11+
- **Framework Web & ORM** : Django 5.x
- **API Engine** : Django REST Framework (DRF) 3.18+
- **Sécurité & Auth** : `djangorestframework-simplejwt` (Tokens JWT avec rotation)
- **Base de Données** : PostgreSQL en production / SQLite en environnement de dev & test local
- **Spécification OpenAPI** : `drf-spectacular` (OpenAPI 3.0 avec Swagger UI & ReDoc)
- **Filtrage et Recherche** : `django-filter`, DRF SearchFilter & OrderingFilter

---

## 2. Découpage Modulaire des Applications

Le backend est structuré sous `apps/` de manière hautement découplée et maintenable :

1. `apps.common` :
   - Modèles de base abstraits (`TimeStampedModel`, `TenantModel`).
   - Gestionnaire d'erreurs d'API unifié (`custom_exception_handler`).
   - Permissions multi-tenant et RBAC (`IsAuthenticatedAndInTenant`, `RolePermission`).
   - Pagination standardisée (`StandardResultsSetPagination`).
   - ViewSet générique sécurisé (`TenantModelViewSet`).

2. `apps.companies` :
   - Entités Entreprises (Tenants).
   - Informations d'identification fiscale, registre de commerce, devise par défaut.

3. `apps.accounts` :
   - Modèle Utilisateur sur-mesure basé sur `AbstractUser` avec authentification par email.
   - Gestion fine des rôles métier (`ADMIN`, `MANAGER`, `CASHIER`, `STOCK_KEEPER`, `ACCOUNTANT`, `AUDITOR`).
   - Endpoints JWT personnalisés (`/api/v1/auth/token/`) intégrant le contexte de l'entreprise et les informations du profil utilisateur.

4. `apps.catalog` :
   - Gestion des Produits, Unités de mesure (`Unit`), et Catégories hiérarchiques.
   - Suivi des prix de revient (cost price), prix de vente, taux de TVA, seuils d'alerte de stock.

5. `apps.partners` :
   - Gestion unifiée des Tiers : Clients (`CUSTOMER`), Fournisseurs (`SUPPLIER`), et Mixtes (`BOTH`).
   - Suivi du plafond de crédit (`credit_limit`) et de l'encours / solde courant (`current_balance`).

6. `apps.inventory` :
   - Dépôts et Magasins (`Store`).
   - Niveaux de stock par magasin et produit (`StockLevel`).
   - Grand livre des stocks avec traçabilité intégrale (`StockMovement`).
   - Campagnes d'inventaire physique (`Inventory`, `InventoryLine`) avec calcul automatique des écarts et régularisation des stocks.

7. `apps.pos` :
   - Terminaux et Caisses physiques ou logiques (`CashRegister`).
   - Gestion des sessions d'ouverture/fermeture de caisse avec contrôle des écarts de caisse (`RegisterSession`).

8. `apps.sales` :
   - En-têtes de ventes et lignes d'articles (`Sale`, `SaleItem`).
   - Règlements multi-moyens (Espèces, CB, Mobile Money, Virement, Chèque, Crédit).
   - Gestion des retours clients (`SaleReturn`, `SaleReturnItem`) et annulations avec réintégration en stock.

9. `apps.purchases` :
   - Commandes et réceptions fournisseurs (`Purchase`, `PurchaseItem`).
   - Retours fournisseurs (`PurchaseReturn`, `PurchaseReturnItem`) et annulations avec déstockage.

10. `apps.reports` :
    - Tableaux de bord Business Intelligence : Chiffre d'affaires, marges brutes estimées, volumes d'achats, alertes stocks critiques.
    - Évaluation et valorisation financière globale des stocks (au coût de revient et au prix de vente).

11. `apps.notifications` :
    - Centre de notifications métier (alertes de réapprovisionnement, validations de ventes, écarts d'inventaire).

12. `apps.audit` :
    - Journal d'audit et de traçabilité immuable (`AuditLog`) consignant toutes les actions sensibles par utilisateur, IP et ressource.

---

## 3. Logique Métier Transactionnelle & Intégrité des Stocks

Pour garantir une architecture saine, aucune logique métier lourde n'est implémentée dans les `views` ou les `serializers`. La logique métier est centralisée dans des **Domain Services** sous `services.py` :

- `StockService` (`apps/inventory/services.py`) :
  - Opérations encapsulées dans des transactions atomiques (`@transaction.atomic`).
  - Verrouillage pessimiste de lignes (`select_for_update()`) pour prévenir les accès concurrents ("race conditions") sur les niveaux de stock.
  - Journalisation systématique des mouvements avant/après (`quantity_before`, `quantity_after`).
  - Interdiction stricte des stocks négatifs sauf régularisation explicite autorisée.

- `SaleService` (`apps/sales/services.py`) :
  - Cycle de vente complet en 6 étapes transactionnelles :
    1. Vérification préalable de la disponibilité du stock pour l'ensemble des articles du panier.
    2. Création de l'en-tête de vente.
    3. Création des lignes de vente et calcul des remises/taxes.
    4. Décrémentation atomique du stock par `StockService`.
    5. Création des lignes de mouvements de stock d'audit.
    6. Traitement immédiat des encaissements et mise à jour du solde de caisse.
  - En cas d'exception ou de rupture de stock, un rollback complet est opéré : aucune ligne orpheline n'est enregistrée.

- `PurchaseService` (`apps/purchases/services.py`) :
  - Gestion des statuts de commandes fournisseurs (Brouillon $\to$ Réceptionné $\to$ Annulé).
  - Incrémentation automatisée et traçable des stocks à la réception des marchandises.

---

## 4. Multi-Tenant (Isolation Stricte des Données)

Le multi-tenant repose sur un partitionnement logique strict par entreprise :
- Tous les modèles métier dérivent de `TenantModel` contenant une clé étrangère non nulle vers `Company`.
- Le ViewSet générique `TenantModelViewSet` applique automatiquement le filtrage :
  `queryset = queryset.filter(company_id=request.user.company_id)`.
- Lors de la création de n'importe quelle ressource, `company_id` est automatiquement assigné à l'entreprise de l'utilisateur connecté.
- Les tentatives de manipulation d'IDs appartenant à un autre tenant sont automatiquement rejetées (HTTP 404 / HTTP 400).

---

## 5. Démarrage Rapide

### Installation des dépendances
```bash
pip install -r requirements.txt
```

### Initialisation de la base de données
```bash
python manage.py migrate
```

### Lancement des tests unitaires et d'intégration
```bash
python manage.py test tests
```

### Génération du schéma OpenAPI
```bash
python manage.py spectacular --file schema.yaml
```

### Démarrage du serveur de développement
```bash
python manage.py runserver 0.0.0.0:8000
```
