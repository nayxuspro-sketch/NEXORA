# NEXORA - Documentation Frontend

## 1. Vue d'ensemble

Le frontend de **NEXORA** est une interface web moderne, réactive et performante pour l'ERP et le Point de Vente (POS) d'entreprise. Il est conçu pour matérialiser le cycle :
$$\text{Vente} \longrightarrow \text{Gestion} \longrightarrow \text{Compréhension} \longrightarrow \text{Anticipation} \longrightarrow \text{Automatisation}$$

### Technologies Clés
- **Framework** : Next.js 14+ (App Router)
- **UI & Rendu** : React 18, TypeScript (typage strict sans compromis)
- **Styling & Design System** : Tailwind CSS, variables CSS sémantiques (mode sombre/clair)
- **Composants d'interface** : Architecture modulaire basée sur shadcn/ui & Lucide Icons
- **Data Fetching & Cache** : TanStack Query v5 (React Query) avec gestion optimiste du cache, invalidations ciblées et loading states
- **Gestion de Formulaires & Validation** : React Hook Form, Zod
- **API Client** : Client typé avec gestion centralisée des erreurs de validation et des jetons d'authentification JWT

---

## 2. Structure du Projet Frontend

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router (Pages & Layouts)
│   │   ├── audit/              # Journal d'audit et de traçabilité
│   │   ├── inventory/          # Niveaux de stocks et mouvements
│   │   ├── partners/           # Clients et Fournisseurs
│   │   ├── pos/                # Point de Vente (Caisse tactile, panier, règlement)
│   │   ├── products/           # Catalogue de produits & seuils d'alerte
│   │   ├── reports/            # Rapports financiers & valorisation
│   │   ├── sales/              # Historique des ventes et factures
│   │   ├── layout.tsx          # Layout racine avec Providers
│   │   ├── page.tsx            # Dashboard décisionnel (KPIs, alertes)
│   │   └── providers.tsx       # TanStack Query, Auth & Toast Providers
│   ├── components/
│   │   ├── layout/             # Sidebar, Topbar, QuickSearch, DashboardLayout
│   │   ├── ui/                 # Boutons, Modales, DataTables, Badges, Cartes KPI, Toasts
│   │   └── shared/             # Composants métier transverses
│   ├── lib/
│   │   ├── api.ts              # Client API REST avec gestion d'erreurs
│   │   ├── auth.tsx            # Contexte d'authentification et session utilisateur
│   │   └── utils.ts            # Utilitaires de formatage (devises, dates)
│   └── types/                  # Définitions TypeScript partagées
├── tailwind.config.js          # Configuration du thème et tokens sémantiques
├── tsconfig.json               # Configuration TypeScript stricte
└── package.json
```

---

## 3. Écrans & Parcours Métier Implémentés

### 1. Dashboard de Gestion (`/`)
- Cartes KPI synthétiques : Chiffre d'affaires 30 jours, Marge brute estimée, Unités physiques en stock, Alertes de rupture imminente.
- Graphique d'évolution hebdomadaire des ventes.
- Encadré d'alertes de réapprovisionnement prioritaires avec indicateurs de criticité.

### 2. Point de Vente & Caisse (`/pos`)
- Conçu pour une utilisation ultra-rapide sur écran tactile, tablette ou ordinateur de caisse.
- Recherche instantanée par nom, SKU ou lecteur de code-barres.
- Gestion du panier en temps réel : calcul des sous-totaux HT, ventilation de la TVA collectée et total TTC.
- Modal d'encaissement multi-moyens (Espèces, Carte bancaire, Mobile Money).
- Rendu de monnaie instantané pour les règlements en espèces.
- Confirmation et traçabilité immédiate de la vente avec décrémentation automatique des stocks.

### 3. Catalogue Produits (`/products`)
- Liste paginée avec recherche dynamique et filtres.
- Affichage du prix de revient, prix de vente, marge théorique et seuil d'alerte.
- Modal de création rapide d'article avec validation des données.

### 4. Stocks & Inventaires (`/inventory`)
- Bascule à double onglet :
  1. **Niveaux de stock actuels** par dépôt/magasin.
  2. **Grand livre immuable des mouvements de stock** traçant chaque entrée/sortie, le type de flux (`SALE`, `PURCHASE`, `ADJUSTMENT`), l'opérateur et la référence.

### 5. Ventes & Règlements (`/sales`)
- Suivi exhaustif des commandes et ventes réalisées.
- Statuts de règlement en temps réel (`PAID`, `PARTIAL`, `PENDING`).

### 6. Répertoire Clients & Fournisseurs (`/partners`)
- Suivi unifié des comptes tiers : encours financier, solde courant et plafonds de crédit autorisés.

### 7. Rapports Financiers & Valorisation (`/reports`)
- Valorisation globale du stock au coût d'achat et au prix de vente potentiel.
- Estimation de la marge brute prévisionnelle et taux de rotation.

### 8. Journal d'Audit (`/audit`)
- Visualisation horodatée de toutes les opérations sensibles pour la conformité et la sécurité.

---

## 4. Expérience Utilisateur (UX) & Ergonomie Mobile

- **Raccourci Clavier Global (`Cmd + K` / `Ctrl + K`)** : Ouvre une palette de commande instantanée pour naviguer dans l'application sans quitter le clavier.
- **Responsive Mobile First** : Barre latérale escamotable, tiroir de menu optimisé et tables à défilement horizontal fluide sur smartphone.
- **Système de Toast Notification** : Retours visuels clairs lors des créations d'articles, ajouts au panier et encaissements.
- **Tolérance Hors-ligne / Données Fallback** : Les vues disposent de données de secours garantissant une expérience fluide même si le backend est momentanément inaccessible.

---

## 5. Commandes de Développement & Production

```bash
# Aller dans le répertoire frontend
cd frontend

# Lancer le serveur de développement Next.js (port 3000)
npm run dev

# Compiler et vérifier les types TypeScript
npm run build

# Démarrer le serveur de production
npm start
```
