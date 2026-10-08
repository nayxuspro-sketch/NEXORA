# NEXORA - Schéma et Architecture de Base de Données

## 1. Modélisation Conceptuelle des Données (MCD)

La base de données repose sur l'isolation multi-tenant stricte. Chaque table métier contient une clé étrangère non nulle vers `Company`.

```
                    ┌─────────────────────────┐
                    │         Company         │
                    │  (Tenant Partitioning)  │
                    └────────────┬────────────┘
                                 │ 1:N
       ┌──────────────┬──────────┴───┬──────────────┬──────────────┐
       ▼              ▼              ▼              ▼              ▼
┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐
│    User    │ │  Product   │ │  Partner   │ │   Store    │ │Automation  │
│   (RBAC)   │ │  (Catalog) │ │(Cust/Supp) │ │ (Depots)   │ │    Rule    │
└────────────┘ └──────┬─────┘ └──────┬─────┘ └──────┬─────┘ └────────────┘
                      │              │              │
                      │ 1:N          │ 1:N          │ 1:N
                      ▼              ▼              ▼
               ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
               │ StockLevel  │ │    Sale     │ │CashRegister │
               │ (Available) │ │   & Items   │ │  & Session  │
               └──────┬──────┘ └──────┬──────┘ └─────────────┘
                      │               │
                      └───────┬───────┘
                              ▼
                     ┌─────────────────┐
                     │  StockMovement  │
                     │(Immutable Audit)│
                     └─────────────────┘
```

---

## 2. Dictionnaire des Tables Principales

| Table SQL | Modèle Django | Clé Primaire | Description & Contraintes Clés |
| :--- | :--- | :---: | :--- |
| `apps_companies_company` | `Company` | UUID | Entité entreprise. Slug unique. Devise par défaut. |
| `apps_accounts_user` | `User` | UUID | Collaborateur. Email unique (login). Rôle RBAC. Clé `company_id`. |
| `apps_catalog_product` | `Product` | UUID | SKU unique par entreprise (`unique_together: company, sku`). Coût, prix vente, seuil d'alerte. |
| `apps_partners_partner` | `Partner` | UUID | Tiers client ou fournisseur. Encours et plafond de crédit. |
| `apps_inventory_store` | `Store` | UUID | Magasin ou entrepôt de stockage. Code unique par entreprise. |
| `apps_inventory_stocklevel` | `StockLevel` | UUID | Quantité physique en stock par couple `(store, product)` unique. |
| `apps_inventory_stockmovement` | `StockMovement` | UUID | Grand livre immuable : quantités avant/après, 11 types de flux, référence, utilisateur. |
| `apps_pos_cashregister` | `CashRegister` | UUID | Terminal de caisse. Solde courant, caissier actif, statut `OPEN/CLOSED`. |
| `apps_sales_sale` | `Sale` | UUID | En-tête de vente : référence unique par entreprise, montants HT/TVA/TTC, statut, client. |
| `apps_sales_saleitem` | `SaleItem` | UUID | Ligne d'article vendu : produit, quantité, prix unitaire, remise ligne, total. |
| `apps_sales_payment` | `Payment` | UUID | Enregistrement du règlement (Espèces, CB, Mobile Money, Crédit). |
| `apps_audit_auditlog` | `AuditLog` | UUID | Journal de sécurité : actions mutantes, connexions, rejets 403, adresse IP. |
| `apps_ai_assistant_automationrule` | `AutomationRule` | UUID | Règles conditionnelles `SI déclencheur -> ALORS action` avec compteurs d'exécution. |

---

## 3. Stratégie d'Indexation & Intégrité Référentielle

- **Clés primaires** : UUIDv4 pour garantir l'absence de collision lors de synchronisations décentralisées ou d'exports/imports.
- **Index composites** :
  - `(company, store, product)` sur `StockLevel` pour des consultations instantanées au point de vente.
  - `(company, reference)` sur `Sale`, `Purchase` et `Inventory` pour l'unicité et la rapidité des recherches.
- **Intégrité en cascade** : La suppression accidentelle d'une ressource parente préserve l'intégrité de l'historique via des clauses `PROTECT` ou `SET_NULL` sur les mouvements comptables et d'audit.
