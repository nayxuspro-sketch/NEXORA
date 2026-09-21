# NEXORA - Règles Métier et Politiques de Gestion des Stocks

## Règle 1 : Transactionnalité et Absence d'États Résiduels
Toute action modifiant un stock (`StockLevel`) doit impérativement s'exécuter sous transaction de base de données atomique (`@transaction.atomic`). En cas d'anomalie ou d'exception à n'importe quel stade, l'intégralité de la transaction est annulée par rollback.

---

## Règle 2 : Interdiction des Stocks Négatifs
Par principe strict de gestion :
- Aucun mouvement de type `SALE` (vente) ou `TRANSFER_OUT` (transfert) ne peut faire passer un stock sous le seuil zéro.
- Si le stock disponible est inférieur à la quantité demandée, l'opération est immédiatement bloquée avec émission d'un message d'erreur clair.
- Seules les régularisations d'inventaire (`ADJUSTMENT_OUT`) autorisent exceptionnellement le paramètre `allow_negative=True` afin de refléter fidèlement une rupture physique constatée.

---

## Règle 3 : Traçabilité Obligatoire Avant / Après
Aucun stock ne peut être modifié par simple mise à jour directe d'une valeur sans émission corrélative d'une ligne dans `StockMovement`. Le grand livre doit afficher :
- Quantité avant l'opération (`quantity_before`)
- Quantité après l'opération (`quantity_after`)
- Identifiant de l'utilisateur ayant opéré
- Document source et motif

---

## Règle 4 : Gestion des Transferts Inter-Dépôts
Un transfert de stock implique obligatoirement deux magasins de la même entreprise :
- Le magasin expéditeur subit un flux sortant négatif `TRANSFER_OUT`.
- Le magasin récepteur subit un flux entrant positif `TRANSFER_IN`.
- La somme algébrique des variations à l'échelle de l'entreprise est nulle.

---

## Règle 5 : Gestion des Pertes, Vols et Casses
- Tout article détruit ou volé doit faire l'objet d'une déclaration immédiate dans le système.
- Les mouvements sont typés spécifiquement (`DAMAGE` pour la casse, `LOSS` pour le vol) afin de dissocier les pertes opérationnelles des démarques commerciales dans les rapports d'audit.

---

## Règle 6 : Seuil de Sécurité et Alertes Préventives
Chaque produit possède un seuil d'alerte (`alert_threshold`) :
- Dès que $\text{Stock Actuel} \le \text{Seuil d'Alerte}$, le système émet une alerte critique sur le tableau de bord et dans le module logistique.
- Si $\text{Stock Actuel} = 0$, l'article passe en état de rupture bloquante à la vente.

---

## Règle 7 : Mention d'Estimation sur les Prévisions
Les estimations prédictives de consommation journalière, d'autonomie et de réapprovisionnement doivent obligatoirement être présentées à l'utilisateur avec la mention légale et ergonomique :
*"Toutes les prévisions et suggestions constituent des estimations indicatives calculées sur la base de l'historique des ventes."*
