# NEXORA — Power BI de zéro à dashboard professionnel

NEXORA est un parcours de formation interactif en français, conçu pour accompagner un débutant absolu jusqu’à la réalisation d’un dashboard Power BI professionnel.

## Contenu

- 12 modules progressifs, du vocabulaire BI au projet final ;
- démonstrations guidées, formules DAX, erreurs fréquentes et bonnes pratiques ;
- exercices guidés, exercices autonomes corrigés et mini-projets ;
- repères « Capture à insérer » pour documenter les écrans Power BI sans inventer de captures ;
- atelier DAX avec les fonctions d’agrégation, de logique, de filtrage et d’analyse temporelle ;
- jeu de données CSV téléchargeable ;
- lexique, carnet de notes local et progression persistante dans le navigateur ;
- **quiz auto-corrigés de 3 questions à la fin de chaque module** (36 questions avec explications) ;
- **export / import de la progression** (modules, quiz et notes) au format JSON ;
- **résilience** : l’application démarre toujours, même si le stockage local est corrompu (valeurs réinitialisées proprement) ;
- **profil personnalisable** (prénom et initiales affichés partout) ;
- **activité hebdomadaire réelle** tracée depuis vos actions (quiz, modules, notes) ;
- **certificat imprimable** débloqué à 12 modules validés ;
- **navigation par URL** : chaque vue a son lien (`#parcours`, `#module/3`) — le bouton retour du navigateur et les favoris fonctionnent ;
- **recherche globale** : menu de résultats groupés (modules, lexique, DAX) avec navigation directe au résultat ;
- **quiz rejouables** : bouton « Recommencer le quiz » après la correction ;
- **navigation de leçon en leçon** : boutons Précédent / Suivant en pied de leçon, avec déblocage automatique du module suivant après validation ;
- **export des notes en Markdown** (`nexora_notes.md`) depuis l’onglet Mes notes ;
- **annexe lexique automatique** dans `manuel.html` : les 48 termes sont injectés depuis `app.js` à chaque construction ;
- **accessibilité clavier** : styles `:focus-visible` sur tous les contrôles ;
- **accès rapide au contenu** (lien d’évitement type skip-link) pour la navigation au clavier ;
- **accessibilité avancée** : `aria-current` sur la vue active, `aria-expanded` sur le menu mobile et respect de `prefers-reduced-motion` dans tous les défilements ;
- **atelier DAX de 18 fiches** : agrégations, comptage, logique, filtrage, temps et statistiques ;
- **manuel HTML lisible et imprimable** : `manuel.html` (généré depuis `FORMATION_POWER_BI.md`) avec sommaire et bouton Imprimer ;
- parcours responsive, utilisable sur desktop et mobile ;
- manuel imprimable complet dans `FORMATION_POWER_BI.md` ;
- jeu de données versionné dans `data/contoso_exercice.csv`.

## Modules

1. Comprendre la Business Intelligence
2. Vos premiers pas dans Power BI Desktop
3. Nettoyer avec Power Query
4. Construire un modèle en étoile
5. DAX : mesures et agrégations
6. DAX : contexte, filtres et temps
7. Choisir les bons visuels
8. Interactions et rapport professionnel
9. Publier avec Power BI Service
10. Sécurité et gouvernance
11. Projet guidé : cockpit commercial
12. Projet final : votre dashboard de référence

## Jeux de données d’exercice

| Fichier | Contenu | Exercices |
|---|---|---|
| `data/contoso_exercice.csv` | Ventes Contoso (12 lignes) | Modules 1–9, 11 |
| `data/contoso_exercice.xlsx` | Ventes Contoso au format Excel (feuille `Ventes`) | Module 2 — import Excel |
| `data/notes_exercice.csv` | Notes scolaires (30 lignes) | Modules 5, 7 |
| `data/commandes_exercice.csv` | Commandes et délais (24 lignes, retards extrêmes inclus) | Modules 6, 7 |
| `data/habilitations_exercice.csv` | Habilitations RLS (10 utilisateurs) | Module 10 |

Téléchargeables depuis l’onglet **Ressources** de l’application.

## Lancer localement

Le projet est statique et ne nécessite aucune dépendance :

```bash
python3 -m http.server 4173 --bind 0.0.0.0
```

Puis ouvrir `http://localhost:4173`.

## Tests

Un test de fumée (navigation, modules, lexique, checklist, notes, progression) est fouri :

```bash
npm install --no-save jsdom
node test/smoke.mjs
```

Il vérifie 118 contrôles (dont l’intégrité des fichiers, téléchargements et ancres du manuel) sans nécessiter de navigateur, dont une **vérification d’intégrité pédagogique** : chaque module possède ses objectifs, sa démonstration, sa formule, ses erreurs, ses exercices et sa correction ; chaque quiz ses 3 questions valides ; chaque fiche DAX ses 6 champs.

## Manuel PDF

`Formation_Power_BI_NEXORA.pdf` (32 pages, couverture, sommaire cliquable avec numéros de page, signets PDF et annexe lexique) :

```bash
pip install --break-system-packages reportlab pypdf
python3 tools/build_pdf.py
```

## Régénérer le manuel HTML

`manuel.html` est généré à partir de `FORMATION_POWER_BI.md` (+ annexe lexique injectée depuis `app.js`) :

```bash
npm install --no-save marked
node tools/build_manual.mjs
```

## Notes pédagogiques

Les captures d’écran Power BI réelles dépendent de la version de Desktop, du système et de la langue installée. L’interface utilise donc des repères clairement marqués **Capture à insérer**, avec une description précise de l’écran attendu plutôt que des images susceptibles d’être trompeuses.
