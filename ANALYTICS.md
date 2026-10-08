# NEXORA - Spécifications Analytiques & Moteur de Calcul

## 1. Modélisation Mathématique des Métriques

### Chiffre d'Affaires Net (Revenu Réel)
$$\text{CA Net} = \sum (\text{Quantité} \times \text{Prix Vente TTC}) - \text{Remises Accordées}$$

### Coût d'Achat des Marchandises Vendues (COGS)
$$\text{COGS} = \sum (\text{Quantité Vendue} \times \text{Coût de Revient Unitaire})$$

### Marge Brute Commerciale
$$\text{Marge Brute} = \text{CA Net (HT)} - \text{COGS}$$

### Taux de Marge (%)
$$\text{Taux de Marge} = \left( \frac{\text{Marge Brute}}{\text{CA Net (HT)}} \right) \times 100$$

### Panier Moyen
$$\text{Panier Moyen} = \frac{\text{CA Total de la période}}{\text{Nombre total de transactions validées}}$$

---

## 2. Décomposition Temporelle & Croissance

Le moteur compare automatiquement la période sélectionnée ($T$) avec la période antérieure équivalente ($T_{-1}$) :
$$\text{Taux d'Évolution (\%)} = \left( \frac{\text{CA}_T - \text{CA}_{T-1}}{\text{CA}_{T-1}} \right) \times 100$$

- Si $\Delta \text{CA} > 0$ et $\Delta \text{Panier} > \Delta \text{Volume}$ $\Rightarrow$ Croissance axée sur la montée en gamme / panier moyen.
- Si $\Delta \text{CA} > 0$ et $\Delta \text{Volume} > \Delta \text{Panier}$ $\Rightarrow$ Croissance tirée par la conquête client / fréquence d'achat.
- Si $\Delta \text{CA} < 0$ $\Rightarrow$ Identification immédiate du facteur prédominant (perte de clients ou baisse du panier).
