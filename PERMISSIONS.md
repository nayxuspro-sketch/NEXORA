# NEXORA - Matrice des Rôles et Permissions (RBAC & Multi-Tenant)

La sécurité de la plateforme NEXORA repose sur deux couches indispensables et complémentaires :
1. **Cloisonnement Multi-Tenant** : Aucun utilisateur ne peut accéder, lire, modifier ou référencer les données d'une autre entreprise.
2. **Contrôle d'Accès Basé sur les Rôles (RBAC)** : Chaque utilisateur possède un rôle précis délimitant ses capacités d'action au sein de son entreprise.

---

## 1. Rôles Définis dans NEXORA

| Identifiant Rôle | Titre Métier | Description |
| :--- | :--- | :--- |
| `ADMIN` | Administrateur Entreprise | Accès complet aux paramètres de l'entreprise, utilisateurs, rapports, finances et gestion des magasins. |
| `MANAGER` | Responsable de Magasin | Gestion des opérations du magasin, validation des inventaires, suivi des stocks, des caisses et des ventes. |
| `CASHIER` | Caissier / Vendeur | Ouverture/fermeture de sa session de caisse, enregistrement des ventes au comptoir et encaissements. |
| `STOCK_KEEPER` | Gestionnaire de Stock | Entrées en stock, réceptions de commandes d'achats, transferts inter-dépôts et saisie des inventaires. |
| `ACCOUNTANT` | Comptable | Suivi des règlements clients/fournisseurs, gestion des crédits partenaires, rapports financiers et valorisation. |
| `AUDITOR` | Auditeur | Consultation en lecture seule des mouvements de stock, des transactions de vente et du journal d'audit. |

---

## 2. Matrice des Droits par Module

| Module / Ressource | Action | ADMIN | MANAGER | CASHIER | STOCK_KEEPER | ACCOUNTANT | AUDITOR |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Utilisateurs & Profils** | Créer / Modifier | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| | Consulter | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Catalogue & Produits** | Créer / Modifier | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| | Consulter | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Clients & Fournisseurs** | Créer / Modifier | ✅ | ✅ | ✅ (Clients) | ❌ | ✅ | ❌ |
| | Consulter | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Point de Vente & Caisse** | Ouvrir / Clôturer Caisse | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| | Visualiser toutes les sessions | ✅ | ✅ | Propre session | ❌ | ✅ | ✅ |
| **Ventes & Encaissements** | Enregistrer une vente | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| | Enregistrer un paiement | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ |
| | Annuler / Retourner | ✅ | ✅ | ❌ (Sur validation) | ❌ | ❌ | ❌ |
| **Achats & Fournisseurs** | Créer commande d'achat | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ |
| | Réceptionner marchandise | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ |
| | Règlement fournisseur | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ |
| **Gestion des Stocks** | Mouvement manuel / Régul | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ |
| | Valider un inventaire | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| | Consulter les stocks | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Rapports & BI** | Tableau de bord financier | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ |
| | Valorisation des stocks | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ |
| **Audit Logs** | Consulter l'historique | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ |

---

## 3. Règles d'Implémentation du Multi-Tenant

1. **Isolation par Clé Étrangère Obligatoire** :
   Chaque table hérite de `TenantModel` avec une liaison stricte `company_id`.

2. **Filtrage Système Automatisé** :
   Dans `apps/common/viewsets.py`, la méthode `get_queryset()` filtre systématiquement `company_id=request.user.company_id`.

3. **Validation Anti-Fuite (Cross-Tenant Integrity)** :
   Lorsqu'un utilisateur soumet des entités associées (ex: un ID produit ou un ID magasin lors d'une vente), le service métier s'assure impérativement que `product.company_id == user.company_id` et `store.company_id == user.company_id`.
   Toute tentative de manipulation entraîne une erreur `400 Bad Request` ou `404 Not Found`.
