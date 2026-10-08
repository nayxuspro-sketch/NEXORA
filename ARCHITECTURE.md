# NEXORA - Architecture Système & Source de Vérité

Ce document constitue la **source de vérité absolue** de l'architecture technique globale de la plateforme **NEXORA**. Tout agent ou développeur doit s'y conformer strictement.

---

## 1. Principes Fondamentaux d'Architecture

1. **Séparation Stricte des Responsabilités (Separation of Concerns)** :
   - Les **Vues (Views)** se limitent à l'acheminement HTTP, la validation de permission et la sérialisation.
   - Les **Serializers** valident la structure et la conformité des flux JSON entrants/sortants.
   - La **Logique Métier** est impérativement centralisée dans des **Domain Services** purs (`StockService`, `SaleService`, `PurchaseService`, `AutomationEngine`, `AIAssistantService`).

2. **Isolation Multi-Tenant Inviolable** :
   - Tout modèle de données applicatif dérive de `TenantModel` (`apps.common.models`).
   - Aucune requête métier ne s'exécute sans liaison explicite avec l'entité `Company`.
   - Les ViewSets héritent de `TenantModelViewSet` qui applique un filtrage automatique `company_id=request.user.company_id`.

3. **Intégrité Transactionnelle ACID** :
   - Toute opération modifiant conjointement plusieurs états (ex: vente + stock + grand livre + caisse) est encapsulée dans une transaction de base de données (`@transaction.atomic`).
   - Le verrouillage pessimiste de lignes (`select_for_update()`) prévient toute condition de concurrence lors des décrémentations de stock simultanées.

---

## 2. Découpage Modulaire des Applications

```
NEXORA/
├── apps/
│   ├── common/         # Primitives abstraites, TenantModel, exceptions, pagination, healthcheck
│   ├── companies/      # Gestion des entreprises clientes (Tenants)
│   ├── accounts/       # Utilisateurs personnalisés (email), rôles RBAC, JWT enrichi
│   ├── catalog/        # Catégories, unités, produits, prix de revient et de vente
│   ├── partners/       # Tiers (Clients, Fournisseurs), encours et plafonds de crédit
│   ├── inventory/      # Magasins, StockLevels, StockMovements (11 flux), inventaires
│   ├── pos/            # Caisses, sessions, raccourcis, suggestions de caisse (cross-selling)
│   ├── sales/          # Ventes, encaissements, remises, retours clients et annulations
│   ├── purchases/      # Commandes fournisseurs, réceptions, règlements et retours
│   ├── reports/        # Tableaux de bord BI, moteurs d'explications en langage naturel
│   ├── notifications/  # Centre de notifications ciblées par collaborateur
│   ├── audit/          # Middleware de sécurité, journal immuable d'audit (AuditLog)
│   └── ai_assistant/   # Assistant conversationnel RBAC, moteur de règles conditionnelles (SI/ALORS)
├── frontend/           # Application Next.js 14 (App Router), Tailwind CSS, TanStack Query
├── config/             # Paramètres Django, URLs versionnées v1, OpenAPI 3.0
├── scripts/            # Scripts d'automatisation (sauvegarde, restauration)
└── tests/              # 31 tests unitaires, d'intégration, logistique et sécurité
```

---

## 3. Contrat d'Interface API & Normalisation

- **Protocole** : REST JSON sur HTTPS
- **Documentation Vivante** : Spécification OpenAPI 3.0 via Swagger UI (`/api/v1/docs/`) et ReDoc (`/api/v1/redoc/`)
- **Format Normalisé des Réponses Paginées** :
  `{ status: "success", pagination: { count, total_pages, current_page, page_size, next, previous }, results: [...] }`
- **Format Normalisé des Erreurs** :
  `{ status: "error", code: "<ERROR_CODE>", message: "<Description>", details: <Dict|List> }`
