# NEXORA - Moteur d'Automatisation & Règles Métier

## 1. Architecture Déclencheur / Action (Trigger-Action Engine)

NEXORA intègre un moteur de règles automatisé reposant sur le formalisme :
$$\text{SI } \langle \text{Condition Détectée} \rangle \longrightarrow \text{ALORS } \langle \text{Action Exécutée} \rangle$$

---

## 2. Déclencheurs Implémentés (`TriggerType`)

| Déclencheur | Description | Paramètres Configurables |
| :--- | :--- | :--- |
| `STOCK_BELOW_THRESHOLD` | Le stock d'un produit passe sous son seuil d'alerte en magasin. | Seuil numérique (`threshold`) |
| `OVERDUE_INVOICE` | Une facture ou créance client dépasse $X$ jours d'impayé. | Nombre de jours d'échéance (`days_overdue`) |
| `LARGE_TRANSACTION` | Une transaction de vente dépasse un montant exceptionnel. | Montant plancher (`target_amount`) |
| `INVENTORY_DISCREPANCY`| Écart d'inventaire significatif constaté lors d'un comptage. | Pourcentage d'écart toléré |

---

## 3. Actions Exécutables (`ActionType`)

| Action | Description | Impact Opérationnel |
| :--- | :--- | :--- |
| `CREATE_NOTIFICATION` | Émet une notification dans le centre d'alertes des responsables. | Alerte visuelle prioritaire |
| `DRAFT_PURCHASE_ORDER`| Génère un bon de commande fournisseur à l'état brouillon. | Prépare le réassort sans engagement financier |
| `LOG_AUDIT_WARNING` | Consigne l'incident dans le registre d'audit de sécurité. | Traçabilité de conformité |

---

## 4. Évaluation & Journalisation Immuable

- Le moteur peut être déclenché automatiquement ou à la demande via `POST /api/v1/automation-rules/trigger_engine/`.
- Chaque exécution est consignée dans `AutomationLog` avec l'horodatage, le statut (`SUCCESS` ou `FAILED`) et les détails structurés des données affectées.
