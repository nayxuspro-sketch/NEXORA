# NEXORA - Moteur de Recommandation & Anticipation

## 1. Algorithmes de Recommandation

Le moteur de recommandation de NEXORA articule trois méthodologies :

### 1. Analyse du Panier de la Ménagère (Cross-Selling / Apriori simplifié)
- **Objectif** : Identifier les produits fréquemment achetés ensemble au comptoir POS.
- **Logique** : À chaque article scanné dans le panier de caisse, le moteur recherche les ventes historiques associées et extrait les produits connexes à plus forte co-occurrence.

### 2. Anticipation du Réapprovisionnement Logistique
- **Formule d'autonomie** :
  $$\text{Jours de Stock Restants} = \frac{\text{Stock Disponible}}{\text{Ventes Journalières Moyennes sur 30j}}$$
- Dès que l'autonomie estimée passe sous 7 jours, une suggestion de réassort prioritaire `URGENT` est injectée dans le planning d'achats.

### 3. Détection des Stocks en Sommeil (Dormant Stock)
- **Condition** : $\text{Stock Actuel} > 0 \quad \text{ET} \quad \text{Ventes sur 30 jours} = 0$.
- **Recommandation** : Action de déstockage, offre groupée ou promotion ciblée pour libérer le fonds de roulement.
