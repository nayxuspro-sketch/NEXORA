# NEXORA - Intelligence Artificielle & Assistant Conversationnel

## 1. Philosophie & Principes Directeurs

Le module IA de NEXORA repose sur la chaîne de valeur :
$$\text{COMPRENDRE} \longrightarrow \text{ANTICIPER} \longrightarrow \text{RECOMMANDER} \longrightarrow \text{AUTOMATISER}$$

L'IA n'est pas une boîte noire autonome : c'est un **copilote d'aide à la décision opérationnelle** transparent, responsable et soumis aux contrôles de permission des utilisateurs.

---

## 2. Capacités de l'Assistant Conversationnel (`/api/v1/ai/chat/`)

L'utilisateur peut interagir en langage naturel pour obtenir des réponses immédiates appuyées sur les données en temps réel :

1. **« Combien ai-je vendu aujourd'hui ? »**
   - Calcule le chiffre d'affaires et le nombre de transactions du jour (00:00 UTC à maintenant).
   - Adapte le périmètre au rôle : le caissier ne voit que ses encaissements ; la direction voit l'entreprise entière.

2. **« Quels sont mes produits les plus rentables ? »**
   - Analyse les marges brutes cumulées (CA - Coût d'achat) sur les 30 derniers jours.
   - Restreint aux profils autorisés (`ADMIN`, `MANAGER`).

3. **« Quels produits risquent de manquer ? »**
   - Scanne les stocks réels par rapport aux seuils d'alerte (`StockLevel.quantity <= Product.alert_threshold`).
   - Identifie les urgences de réapprovisionnement.

4. **« Résume mon activité. »**
   - Synthétise les ventes des 7 derniers jours et l'état de santé logistique.

5. **« Quels produits sont dormants ? »**
   - Détecte les stocks positifs n'ayant généré aucune vente sur les 30 derniers jours pour préconiser des actions de déstockage.

---

## 3. Cadre d'Explicabilité Systématique

Chaque recommandation ou synthèse chiffrée fournie par l'IA comprend obligatoirement 4 piliers d'explicabilité :
- **Source des données** : Tables précises consultées (`SaleItem`, `StockLevel`, `Product`).
- **Période analysée** : Fenêtre temporelle exacte (ex: 30 jours glissants).
- **Logique de calcul** : Formule mathématique ou règle appliquée.
- **Limites & Hypothèses** : Précision que le coût d'achat retenu est le coût standard catalogue, hors frais généraux de structure.

---

## 4. IA Responsable & Souveraineté Humaine

- **Aucune décision critique unilatérale** : L'IA ne passe jamais commande ou ne modifie jamais les tarifs de manière irréversible sans validation explicite d'un utilisateur humain habilité.
- **Transparence prédictive** : Toute estimation est expressément étiquetée comme **indicative**.
