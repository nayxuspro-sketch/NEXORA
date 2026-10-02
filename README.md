# NEXORA

Plateforme Vente SAAS.

## Module « Configurer les Droits : Direction & Administration Générale »

Écran de gestion des habilitations, **intégralement en français (`fr-FR`)** : tous les
libellés (titre, onglets, colonnes, niveaux d'accès, portées, actions, messages, aides
et textes d'accessibilité) sont en français.

### Contenu

| Fichier | Rôle |
| --- | --- |
| `index.html` | Fenêtre modale : titre, bandeau de contexte, onglets, corps, récapitulatif latéral, pied de fenêtre |
| `donnees.js` | Référentiels métier en français : niveaux, portées, actions, modules et droits, circuits de validation, profils, historique, règles de séparation des tâches |
| `app.js` | Logique d'affichage et d'interaction (recherche, matrice, récapitulatif, export JSON, impression, notifications) |
| `styles.css` | Mise en forme |
| `i18n/fr-FR.json` | Toutes les chaînes de la fenêtre, externalisées en français (réutilisable dans une autre technologie : `.resx`, `.properties`, fichier de langue, etc.) |

### Périmètre de droits couvert

- Direction Générale
- Administration Générale
- Ressources Humaines
- Finances & Comptabilité
- Achats & Approvisionnements
- Juridique & Conformité
- Services Généraux & Patrimoine
- Informatique & Sécurité

### Onglets de la fenêtre

1. **Matrice des droits** — niveau d'accès (Aucun, Lecture, Création, Modification, Suppression, Accès complet), portée, actions autorisées, état, indicateur « Modifié ».
2. **Circuits de validation** — seuils d'engagement en FCFA, validateur, second validateur, délai, règle au-delà du seuil, délégation & suppléance.
3. **Profils & modèles** — modèles prêts à l'emploi (Direction Générale, Secrétaire Général, DAF, Assistant(e) de Direction, Responsable RH, Contrôleur de gestion, Auditeur interne).
4. **Historique des modifications** — traçabilité des changements de droits.

### Exécution locale

Aucune dépendance ni étape de compilation :

```bash
python3 -m http.server 8000 --bind 0.0.0.0
# puis ouvrir http://localhost:8000
```
