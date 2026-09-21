# NEXORA - Procédures et Campagnes d'Inventaire

## 1. Objectifs de l'Inventaire

L'inventaire physique a pour mission de :
- Rapprocher le **stock théorique** (comptable / informatique) et le **stock réel** (physique en rayon/dépôt).
- Mesurer les écarts d'inventaire (pertes, erreurs de saisie, démarque inconnue).
- Régulariser automatiquement le grand livre sans rupture de traçabilité.

---

## 2. Types d'Inventaires Supportés

### 1. Inventaire Général Complet (`FULL`)
- Blocage temporaire ou arrêt des opérations sur le dépôt audité.
- Comptage exhaustif de 100% des références cataloguées.
- Clôture avec génération des écritures de régularisation comptable.

### 2. Inventaire Tournant / Partiel (`PARTIAL`)
- Réalisé de façon continue tout au long de l'année par famille de produits, marque ou rayon spécifique.
- Ne bloque pas l'activité commerciale globale du magasin.
- Idéal pour les références à forte valeur unitaire ou à risque élevé de démarque.

---

## 3. Workflow d'un Inventaire dans NEXORA

1. **Création de la session** (`status = DRAFT`) :
   - Choix du magasin et du type d'inventaire (`FULL` ou `PARTIAL`).
   - Génération d'une référence unique (`INV-AAAA-NNN`).
2. **Phase de Comptage** (`status = IN_PROGRESS`) :
   - Saisie manuelle ou par scan de code-barres de chaque produit compté (`counted_quantity`).
   - Enregistrement du stock théorique attendu au moment du comptage (`expected_quantity`).
3. **Calcul des Écarts** :
   $$\text{Écart} = \text{Quantité Comptée} - \text{Quantité Théorique}$$
4. **Validation et Clôture Transactionnelle** (`status = VALIDATED`) :
   - Les lignes avec écart non nul émettent automatiquement un mouvement de régularisation :
     - Si $\text{Écart} > 0$ : Mouvement `ADJUSTMENT_IN` (gain de stock).
     - Si $\text{Écart} < 0$ : Mouvement `ADJUSTMENT_OUT` (perte ou coulage).
   - L'inventaire est verrouillé en écriture et archivé avec la signature de l'auditeur.
