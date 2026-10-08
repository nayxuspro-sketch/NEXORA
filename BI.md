# NEXORA - Business Intelligence & Architecture Décisionnelle

## 1. Philosophie & Cadre Décisionnel

Le module de Business Intelligence de NEXORA concrétise le principe directeur :
$$\text{Données Brutes} \longrightarrow \text{Information Structurée} \longrightarrow \text{Compréhension Contextuelle} \longrightarrow \text{Prise de Décision Éclairée}$$

NEXORA ne se contente pas de stocker des chiffres : il **explique les causes** des variations observées sans jamais confisquer la souveraineté décisionnelle du dirigeant.

---

## 2. Dashboards Adaptés par Rôle Métier

L'interface de pilotage s'adapte automatiquement ou sur sélection aux prérogatives de chaque acteur :

| Profil / Rôle | Dashboard Dédié | Indicateurs Prioritaires |
| :--- | :--- | :--- |
| **Direction Générale (`ADMIN`)** | Dashboard Direction | CA global, croissance relative, marge nette estimée, santé de la trésorerie et rentabilité globale. |
| **Gérant de Magasin (`MANAGER`)** | Performance Magasin | Volume des ventes locales, respect des marges cibles, productivité horaire, écarts de caisse. |
| **Commercial / Vente (`SALES`)** | Performance Commerciale | Chiffre d'affaires individuel, volume de commandes signées, taux de conversion des devis. |
| **Responsable Stock (`STOCK_KEEPER`)** | Rotation & Logistique | Valeur du stock immobilisé, vitesse de rotation, articles dormants, taux de rupture. |
| **Caissier (`CASHIER`)** | Caisses & Comptoir | Panier moyen par transaction, vitesse d'encaissement, écarts de fond de caisse. |

---

## 3. Moteur d'Explications Basé sur les Données (Analytics Explicatif)

Au lieu d'un affichage passif tel que `CA = 48 950 €`, l'endpoint `/api/v1/reports/bi-analytics/` décompose automatiquement les causes premières :
- **Hausse tirée par le panier moyen** vs **Hausse par le volume** :
  *« Le CA progresse de +14.2%, principalement soutenu par la hausse du panier moyen (344,71 € vs 280,00 €) malgré un volume de transactions constant. »*
- **Concentration du risque produit** :
  *« L'article 'Ordinateur Portable Pro 15' concentre 48% des recettes de la période. »*
- **Corrélation Stock-Vente** :
  *« 2 références à forte rotation présentent un risque immédiat d'épuisement sous 48h. »*
