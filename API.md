# NEXORA - Documentation de l'API REST v1

L'API REST de NEXORA est conçue selon les standards OpenAPI 3.0, sécurisée par des jetons JWT et isolée par entreprise (multi-tenant).

## 1. Documentation Interactive & Schéma OpenAPI

- **Swagger UI** : `/api/v1/docs/`
- **ReDoc** : `/api/v1/redoc/`
- **Spécification OpenAPI (YAML/JSON)** : `/api/v1/schema/`

---

## 2. Format Standardisé des Réponses et des Erreurs

### En cas de succès paginé
```json
{
  "status": "success",
  "pagination": {
    "count": 42,
    "total_pages": 3,
    "current_page": 1,
    "page_size": 20,
    "next": "http://api.nexora.local/api/v1/products/?page=2",
    "previous": null
  },
  "results": [ ... ]
}
```

### En cas d'erreur normalisée
```json
{
  "status": "error",
  "code": "validation_error",
  "message": "Données invalides ou règles métier non respectées.",
  "details": {
    "quantity": ["Ce champ est obligatoire."]
  }
}
```

---

## 3. Authentification & Sécurité

L'authentification s'effectue via Bearer Token JWT :
`Authorization: Bearer <ACCESS_TOKEN>`

### Obtenir un token
**POST** `/api/v1/auth/token/`
```json
{
  "email": "admin@alpha.com",
  "password": "Password123!"
}
```
**Réponse :**
```json
{
  "access": "<access_token>",
  "refresh": "<refresh_token>",
  "user": {
    "id": "c1f7a0b5-7785-4df3-b8be-b003a2fc15ea",
    "email": "admin@alpha.com",
    "first_name": "Admin",
    "last_name": "Alpha",
    "role": "ADMIN",
    "company_id": "763cb535-6490-48b2-b430-84cf80fae6e9",
    "company_name": "Nexora Alpha SARL"
  }
}
```

### Rafraîchir un token
**POST** `/api/v1/auth/token/refresh/`
```json
{
  "refresh": "<refresh_token>"
}
```

---

## 4. Principaux Endpoints de l'API

### Entreprises & Utilisateurs
- `GET /api/v1/companies/` : Liste de l'entreprise connectée (ou toutes pour super-admin)
- `GET /api/v1/users/` : Liste des collaborateurs de l'entreprise (filtrable par `role`, `is_active`)
- `POST /api/v1/users/` : Création d'un collaborateur
- `GET /api/v1/users/me/` : Informations sur l'utilisateur actuellement authentifié

### Catalogue de Produits
- `GET /api/v1/categories/` : Arborescence des catégories de produits
- `GET /api/v1/units/` : Unités de mesure (pièce, kg, litre, etc.)
- `GET /api/v1/products/` : Liste des produits (filtres: `category`, `is_active`, recherche sur nom/sku/barcode)
- `POST /api/v1/products/` : Création de produit

### Partenaires (Clients & Fournisseurs)
- `GET /api/v1/partners/` : Liste des partenaires (filtres: `partner_type=CUSTOMER|SUPPLIER|BOTH`)
- `POST /api/v1/partners/` : Création d'un tiers

### Magasins & Gestion des Stocks
- `GET /api/v1/stores/` : Liste des magasins et dépôts de stockage
- `GET /api/v1/stock-levels/` : Niveaux de stock actuels par magasin et produit
- `GET /api/v1/stock-movements/` : Historique exhaustif et immuable des flux de stock
- `POST /api/v1/inventories/` : Initialiser une session d'inventaire
- `POST /api/v1/inventories/{id}/add_line/` : Saisir un comptage physique
- `POST /api/v1/inventories/{id}/validate/` : Valider l'inventaire et appliquer automatiquement les écarts en stock

### Caisses Enregistreuses & Point de Vente (POS)
- `GET /api/v1/registers/` : Terminaux de caisse
- `POST /api/v1/registers/{id}/open_session/` : Ouvrir une session de caisse avec fond de caisse initial
- `POST /api/v1/registers/{id}/close_session/` : Clôturer la session de caisse avec calcul de l'écart
- `GET /api/v1/sessions/` : Historique des sessions de caisses

### Ventes & Encaissements
- `GET /api/v1/sales/` : Liste des ventes
- `POST /api/v1/sales/` : Exécution transactionnelle d'une vente :
```json
{
  "store": "d2a09c2a-9e11-4770-b461-19b88ef71661",
  "customer": "b9687e35-a50d-4fd2-895c-941160b729fb",
  "register": "9ff50ce0-b4ef-4b4f-8e2b-fdbd5e94b0d0",
  "items": [
    {
      "product": "2f494921-2e21-4f16-b8c1-6b4539ef2a29",
      "quantity": 2,
      "unit_price": "800.00",
      "tax_rate": "20.00",
      "discount_rate": "0.00"
    }
  ],
  "payment": {
    "amount": "1920.00",
    "method": "CASH",
    "reference": "FAC-001"
  }
}
```
- `POST /api/v1/sales/{id}/pay/` : Enregistrer un règlement complémentaire ou partiel
- `POST /api/v1/sales/{id}/cancel/` : Annuler une vente avec réintégration automatique des stocks
- `POST /api/v1/sales/{id}/return_items/` : Effectuer un retour client partiel ou total
- `GET /api/v1/sale-returns/` : Liste des retours clients

### Achats & Réceptions Fournisseurs
- `GET /api/v1/purchases/` : Liste des commandes d'achats
- `POST /api/v1/purchases/` : Création d'une commande fournisseur
- `POST /api/v1/purchases/{id}/receive/` : Valider la réception physique et approvisionner le stock
- `POST /api/v1/purchases/{id}/pay/` : Régler la facture fournisseur
- `POST /api/v1/purchases/{id}/cancel/` : Annuler la commande
- `POST /api/v1/purchases/{id}/return_items/` : Retourner des articles non conformes au fournisseur

### Rapports & Business Intelligence
- `GET /api/v1/reports/dashboard/?days=30` : Vue consolidée KPI (CA, charges d'achats, marge brute, alertes stock bas)
- `GET /api/v1/reports/inventory-valuation/` : Valorisation globale du stock (au coût d'achat et au prix de vente)

### Notifications & Journal d'Audit
- `GET /api/v1/notifications/` : Liste des alertes de l'utilisateur connecté
- `POST /api/v1/notifications/{id}/mark_read/` : Marquer une notification comme lue
- `POST /api/v1/notifications/mark_all_read/` : Marquer tout comme lu
- `GET /api/v1/audit-logs/` : Journal d'audit (réservé aux rôles ADMIN, MANAGER, AUDITOR)
