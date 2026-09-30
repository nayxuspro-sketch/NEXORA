# NEXORA - Gestion Intelligente des Stocks & Pilotage Logistique

## 1. Vision & Philosophie

NEXORA transforme la gestion des stocks :
$$\text{De « simple quantité disponible »} \longrightarrow \text{En « système proactif de pilotage des ressources »}$$

Le module de stock unifie la traçabilité physique, l'intégrité transactionnelle multi-dépôts et un moteur d'anticipation des besoins en approvisionnement.

---

## 2. Typologie Exhaustive des Mouvements de Stock

Chaque variation de stock est explicitement typée et horodatée :

| Type de Mouvement | Code Interne | Sens | Description |
| :--- | :--- | :---: | :--- |
| **Achat / Réception** | `PURCHASE` | **+** | Entrée de marchandise suite à commande fournisseur. |
| **Vente Comptoir / POS** | `SALE` | **-** | Sortie immédiate à l'encaissement d'une vente client. |
| **Retour Client** | `RETURN_CUSTOMER` | **+** | Réintégration en rayon d'un article restitué. |
| **Retour Fournisseur** | `RETURN_SUPPLIER` | **-** | Expédition d'articles défectueux ou non conformes. |
| **Transfert Entrant** | `TRANSFER_IN` | **+** | Arrivée de marchandise en provenance d'un autre dépôt. |
| **Transfert Sortant** | `TRANSFER_OUT` | **-** | Départ de marchandise vers un magasin distant. |
| **Ajustement Positif** | `ADJUSTMENT_IN` | **+** | Régularisation suite à excédent d'inventaire. |
| **Ajustement Négatif** | `ADJUSTMENT_OUT` | **-** | Régularisation suite à déficit d'inventaire. |
| **Perte / Vol** | `LOSS` | **-** | Disparition inexpliquée ou vol avéré. |
| **Casse / Dépréciation**| `DAMAGE` | **-** | Produit détérioré, périmé ou impropre à la vente. |
| **Stock Initial** | `INITIAL` | **+** | Paramétrage initial lors de la création du produit. |

---

## 3. Grand Livre Immuable & Traçabilité Complète

Chaque enregistrement dans `StockMovement` consigne obligatoirement :
1. **Produit** (SKU, libellé, prix de revient unitaire).
2. **Quantité mouvementée** (positive ou négative).
3. **Stock Avant** (`quantity_before`).
4. **Stock Après** (`quantity_after`).
5. **Magasin / Dépôt source**.
6. **Utilisateur / Opérateur** responsable.
7. **Document Source** (Facture, Bon de livraison, Ticket de caisse, Procès-verbal d'inventaire).
8. **Motif détaillé** de l'opération.

---

## 4. Architecture Multi-Magasins

- **Isolation par dépôt** : Chaque magasin (`Store`) dispose de ses propres niveaux de stocks (`StockLevel`).
- **Transferts Atomiques** : Un transfert entre deux magasins exécute conjointement la sortie (`TRANSFER_OUT`) et l'entrée (`TRANSFER_IN`) au sein d'une seule transaction SQL.

---

## 5. Moteur d'Intelligence & Anticipation Prédictive

Le moteur d'intelligence (`/api/v1/inventory/intelligence/`) analyse en continu les 30 derniers jours d'activité pour calculer :

### Classification par Vitesse de Rotation
- **Forte Rotation (Fast-Moving)** : Produits à fort débit représentant le cœur du chiffre d'affaires.
- **Faible Rotation (Slow-Moving)** : Produits dont l'écoulement nécessite une attention commerciale.
- **Stocks Dormants (Dead Stock)** : Articles n'ayant enregistré aucune vente sur la période, immobilisant inutilement la trésorerie.

### Estimation Prévisionnelle du Réapprovisionnement
Pour chaque article consommé, le moteur calcule :
- La **consommation quotidienne moyenne** :
  $$\text{Conso. Journalière} = \frac{\text{Ventes totales sur 30 jours}}{30}$$
- L'**autonomie résiduelle** en jours :
  $$\text{Autonomie} = \frac{\text{Stock actuel}}{\text{Conso. Journalière}}$$
- La **quantité de commande suggérée** pour garantir un volant de sécurité de 30 jours :
  $$\text{Commande suggérée} = (\text{Conso. Journalière} \times 30) - \text{Stock actuel}$$

> **Mention Légale & UX Obligatoire** : Toutes les prévisions et suggestions de réapprovisionnement sont expressément identifiées comme des **estimations indicatives**.
