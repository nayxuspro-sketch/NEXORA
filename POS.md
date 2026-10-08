# NEXORA - Point de Vente Intelligent (POS)

## 1. Vue d'ensemble du Module POS

Le module de **Point de Vente Intelligent (POS)** de NEXORA est conçu pour les environnements de vente au détail et comptoirs à forte cadence. Il allie une vitesse d'exécution extrême, une ergonomie tactile et clavier, et des fonctionnalités d'anticipation commerciale :

$$\text{Scan Produit} \longrightarrow \text{Panier Dynamique} \longrightarrow \text{Paiement & Monnaie} \longrightarrow \text{Validation Atomique} \longrightarrow \text{Reçu Imprimé / Numérique}$$

---

## 2. Modes d'Acquisition & Scanners Supportés

1. **Lecteur de Code-Barres USB / Sans Fil (HID Keyboard Emulation)** :
   - Dès qu'un code EAN-13, UPC ou SKU est scanné, il est capturé instantanément dans le champ actif sans nécessiter de clic préalable.
2. **Scan Caméra & QR Code Embarqué** :
   - Déclenchable d'un clic pour les smartphones et tablettes via webcam ou objectif intégré.
3. **Recherche Textuelle Instantanée** :
   - Recherche sur le SKU, le nom d'article ou le code-barres avec filtrage réactif et indexation en cache.

---

## 3. Raccourcis Clavier Vendeur

Pour maximiser la productivité et permettre au caissier de ne jamais quitter le clavier :

| Touche | Action | Description |
| :--- | :--- | :--- |
| **`F2`** | Focus Recherche | Place immédiatement le curseur dans le champ de recherche / scan. |
| **`F4`** | Assigner Client | Ouvre la fenêtre modale de sélection de client (nom, crédit disponible). |
| **`F8`** | Écran Règlement | Déclenche la modale de paiement (Espèces, Carte, Mobile Money, Crédit). |
| **`F10`** | Validation Express | Valide et finalise instantanément la transaction. |
| **`ESC`** | Fermer / Annuler | Ferme la modale active ou vide les saisies contextuelles. |

---

## 4. Intelligence Commerciale & Suggestions Discrètes

Le point de vente intègre une couche de recommandation connectée au backend (`/api/v1/pos/suggestions/`) :
- **Produits Fréquemment Achetés Ensemble** : Détection des paniers complémentaires (cross-selling) basée sur l'historique réel des ventes.
- **Offres et Promotions Disponibles** : Affichage discret de packs ou remises immédiates pour inciter à la montée en gamme sans ralentir la caisse.
- Les suggestions n'interrompent jamais la saisie et peuvent être ajoutées au panier d'un seul clic ou raccourci.

---

## 5. Gestion Financière & Règlements

- **Multi-moyens de paiement** :
  - Espèces avec **calcul automatique de la monnaie à rendre**.
  - Carte Bancaire (TPE).
  - Mobile Money.
  - Vente à crédit (avec contrôle automatique du plafond de crédit accordé au client sélectionné).
- **Remises** :
  - Remise en pourcentage à la ligne d'article.
  - Remise globale ticket (`0%`, `5%`, `10%`, ou personnalisée).
- **Ventilation Fiscale** : Calcul automatique et transparent du sous-total HT, de la TVA collectée et du net TTC.

---

## 6. Fiabilité & Intégrité Transactionnelle

À la validation d'une vente :
1. Vérification transactionnelle de la disponibilité des stocks en magasin (`select_for_update()`).
2. Enregistrement de l'en-tête de vente et des lignes d'articles.
3. Décrémentation automatique du stock en temps réel via le `StockService`.
4. Émission d'un mouvement de stock d'audit type `SALE`.
5. Ajustement automatique du solde de la caisse ouverte (`CashRegister.current_balance`).
6. Si échec ou rupture, rollback intégral sans état résiduel.

---

## 7. Reçu Numérique & Impression

- Génération d'un ticket de caisse format thermique (standard 80mm).
- Horodatage certifié, référence unique de transaction, récapitulatif fiscal complet.
- Déclenchement direct de l'impression physique (`window.print()`) ou consultation numérique.
