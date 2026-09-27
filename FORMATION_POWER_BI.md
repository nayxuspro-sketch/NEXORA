# Formation Power BI — de zéro à dashboard professionnel

> Manuel compagnon de l’academy NEXORA. Ce document peut être lu seul ou utilisé avec `index.html` pour suivre les exercices interactifs.

## Comment utiliser ce manuel

La progression suit toujours le même mouvement : **comprendre → observer → manipuler → pratiquer → appliquer → approfondir**. Ne sautez pas directement aux formules DAX. Un calcul juste sur un mauvais modèle reste un mauvais résultat.

Dans l’application NEXORA, chaque module se termine par un **quiz auto-corrigé de 3 questions** avec explications : validez le quiz avant de marquer le module terminé, puis exportez votre progression depuis l’onglet Ressources si vous changez de navigateur.

Chaque chapitre contient : objectifs, prérequis, notions, démonstration, formules, erreurs fréquentes, bonnes pratiques, exercices et mini-projet. Les mentions **Capture à insérer** décrivent précisément l’image à réaliser dans la version de Power BI Desktop utilisée.

---

## Parcours et projet fil rouge

| Module | Sujet | Livrable |
|---|---|---|
| 1 | Business Intelligence | Fiche de cadrage |
| 2 | Power BI Desktop | Premier rapport |
| 3 | Sources et Power Query | Requête nettoyée |
| 4 | Modèle en étoile | Modèle relationnel |
| 5 | Mesures et agrégations DAX | Socle de KPI |
| 6 | Contexte, filtres et temps | Analyse N / N-1 |
| 7 | Statistiques et visualisation | Page d’analyse |
| 8 | Interactions et UX | Rapport navigable |
| 9 | Power BI Service | Rapport publié |
| 10 | Sécurité et gouvernance | Matrice des habilitations |
| 11 | Projet guidé commercial | Cockpit de direction |
| 12 | Projet final | Dashboard de portfolio |

### Jeu de données fil rouge

Le projet utilise une table de faits `F_Ventes` et quatre dimensions :

- `F_Ventes` : `IDVente`, `DateVente`, `IDProduit`, `IDClient`, `IDRegion`, `Quantite`, `Montant`, `Cout` ;
- `D_Produit` : `IDProduit`, `Produit`, `Categorie`, `Segment`, `PrixUnitaire` ;
- `D_Client` : `IDClient`, `Client`, `Secteur`, `Ville` ;
- `D_Region` : `IDRegion`, `Region`, `Pays` ;
- `D_Date` : `Date`, `Année`, `Mois`, `NumMois`, `Trimestre`.

**Granularité de `F_Ventes` : une ligne représente une ligne de vente pour un produit, un client et une date.** Cette phrase doit être écrite avant toute mesure.

---

# Chapitre 1 — Comprendre la Business Intelligence

## Objectifs

À la fin du chapitre, vous saurez définir donnée, information, indicateur et décision ; expliquer le rôle de Power BI ; et décrire les étapes d’un projet analytique.

## Prérequis

Aucun. Le chapitre s’adresse à une personne qui n’a jamais ouvert Power BI.

## Introduction

Une organisation produit des données lorsqu’elle vend un produit, enregistre une absence, reçoit une note ou paie une facture. Une donnée isolée est une trace. La Business Intelligence, ou **BI**, organise ces traces afin d’aider quelqu’un à prendre une décision.

La différence peut se résumer ainsi :

- **Donnée :** `120 unités vendues le 12/09/2026` ;
- **Information :** `les ventes de la gamme A progressent de 18 %` ;
- **Décision :** `renforcer le stock de la gamme A dans la région Nord`.

Power BI n’est pas un décideur automatique. C’est un ensemble d’outils qui prépare, modélise, analyse et présente la donnée.

## Notions fondamentales

### Les trois briques de Power BI

1. **Power BI Desktop** est l’atelier local : connexion aux sources, Power Query, modèle, DAX et rapport.
2. **Power BI Service** est l’espace web : publication, partage, actualisation, applications et gouvernance.
3. **Power BI Mobile** permet de consulter les rapports sur téléphone ou tablette.

Une comparaison simple : Desktop est la cuisine, le Service est le restaurant et le rapport est le menu servi au bon public.

### Le cycle d’un projet BI

1. Partir d’une décision à améliorer.
2. Identifier les sources et leur propriétaire.
3. Nettoyer et transformer les données.
4. Construire un modèle fiable.
5. Créer des mesures et vérifier les résultats.
6. Concevoir une expérience de lecture.
7. Publier, sécuriser, actualiser et maintenir.

## Démonstration pratique

Prenez la phrase « Je veux un dashboard des ventes » et transformez-la en cahier des charges :

1. Qui consultera le rapport ?
2. Quelle décision doit être prise chaque semaine ?
3. Quels produits, régions et périodes doivent être comparés ?
4. Quelle source fait foi ?
5. À quelle fréquence la donnée doit-elle être actualisée ?

### Capture à insérer

Un schéma en cinq blocs : **Sources → Power Query → Modèle → Rapport → Power BI Service**, avec une courte légende sous chaque bloc.

## Formule / indicateur clé

```DAX
Variation % = DIVIDE([Ventes N] - [Ventes N-1], [Ventes N-1], 0)
```

`DIVIDE` protège le calcul lorsque la valeur de référence vaut zéro. Le troisième argument `0` est la valeur de remplacement.

## Erreurs fréquentes

- Construire des graphiques avant d’identifier les décisions à éclairer.
- Utiliser un KPI sans définition écrite.
- Présenter une donnée comme certaine sans vérifier sa source, sa date ou sa couverture.

## Bonnes pratiques

- Écrire un mini-dictionnaire métier avant de commencer.
- Limiter la page principale aux indicateurs utiles à la décision.
- Afficher la source et la date d’actualisation.

## Exercices

**Guidé :** choisissez une activité réelle et écrivez trois décisions, trois questions d’analyse et un indicateur pour chaque question.

**Autonome :** une direction d’école demande « un rapport des élèves ». Proposez quatre indicateurs, leur définition et la décision associée.

**Correction indicative :** taux d’assiduité → contacter les élèves à risque ; effectif par niveau → anticiper les classes ; moyenne par matière → organiser le soutien ; évolution des inscriptions → ajuster la communication.

## Mini-projet

Rédigez une fiche de cadrage d’une page : contexte, public, décisions, indicateurs, sources, fréquence, confidentialité et résultat attendu.

---

# Chapitre 2 — Power BI Desktop et premier rapport

## Objectifs

Installer Desktop, repérer les vues Rapport / Données / Modèle, importer un fichier Excel ou CSV et produire un premier visuel.

## Prérequis

Chapitre 1 et un fichier de données. Aucun prérequis en programmation.

## Notions fondamentales

Dans la **vue Rapport**, on place les visuels. Dans la **vue Données**, on inspecte les lignes et les types. Dans la **vue Modèle**, on voit les relations. Le fichier `.pbix` conserve le modèle, les requêtes, les mesures et les pages de rapport.

Une colonne déposée dans un visuel peut être agrégée par Somme, Moyenne, Nombre, Nombre distinct ou ne pas être résumée. Le choix doit correspondre à la question.

## Démonstration : Excel vers Power BI

1. Ouvrir Power BI Desktop.
2. Choisir **Accueil → Obtenir les données → Excel**.
3. Sélectionner `Contoso.xlsx`.
4. Dans le navigateur, cocher `Ventes` puis choisir **Transformer les données** si la source doit être nettoyée, ou **Charger** si elle est déjà propre.
5. Dans la vue Rapport, choisir un histogramme.
6. Déposer `Categorie` dans l’axe et `Montant` dans les valeurs.
7. Ajouter un titre et activer les étiquettes de données.
8. Enregistrer sous `Contoso_Premier_Rapport.pbix`.

**Résultat attendu :** les barres représentent le chiffre d’affaires de chaque catégorie et une infobulle indique la valeur au survol.

### Capture à insérer

L’interface Desktop : ruban en haut, icônes Rapport / Données / Modèle à gauche, canevas au centre, volets Données, Visualisations et Filtres à droite.

## Formule

```DAX
Total Ventes = SUM(F_Ventes[Montant])
```

- `Total Ventes` est le nom de la mesure.
- `=` affecte le calcul au nom.
- `SUM` additionne.
- `F_Ventes[Montant]` désigne la colonne Montant de la table F_Ventes.

## Erreurs fréquentes

- Importer une feuille Excel avec plusieurs titres, sous-totaux et cellules fusionnées.
- Mettre une colonne texte dans Valeurs et obtenir un comptage inattendu.
- Oublier d’enregistrer le `.pbix`.

## Bonnes pratiques

Nommer les tables, contrôler les types, préférer les tables Excel nommées aux plages libres et masquer les colonnes techniques qui ne servent pas au lecteur.

## Exercices

**Guidé :** créez une carte `Total Ventes`, un histogramme par région et un tableau des ventes récentes. Vérifiez le total avec Excel.

**Autonome :** importez un fichier de dépenses et produisez une carte du total, un visuel par catégorie et un tableau des dix dernières dépenses.

**Correction :** `Montant` doit être numérique, `Date` doit être de type Date et le visuel par catégorie doit appliquer une agrégation cohérente.

## Mini-projet

Livrez une page « Première lecture » : trois cartes KPI, deux visuels, un titre, une période et une note indiquant la source.

---

# Chapitre 3 — Sources, Excel, SQL et Power Query

## Objectifs

Importer différentes sources, nettoyer une table, comprendre les étapes appliquées, distinguer Ajouter et Fusionner et lire le langage M.

## Prérequis

Savoir importer un fichier et reconnaître une colonne numérique, texte ou date.

## Comprendre Power Query

Power Query agit **avant** le modèle. Chaque clic crée une étape enregistrée et rejouable : c’est une recette de nettoyage. Une requête n’est pas seulement un résultat ; c’est la description de la transformation entre la source et la table finale.

### Sources courantes

- **Excel :** idéal pour un prototype ou une petite source structurée ; utiliser des tables nommées.
- **CSV :** vérifier séparateur, encodage, décimales et en-têtes.
- **Dossier :** pratique pour empiler des fichiers mensuels de même structure.
- **SQL Server :** adapté aux volumes, aux sources partagées et aux requêtes contrôlées.
- **SharePoint, API, services cloud :** documenter identifiants, propriétaire et fréquence.

### Ajouter ou Fusionner ?

- **Ajouter des requêtes** empile des lignes ayant les mêmes colonnes : janvier + février.
- **Fusionner des requêtes** rapproche des colonnes grâce à une clé : ventes + nom du produit.

## Démonstration : nettoyer les ventes

1. **Accueil → Transformer les données**.
2. Sélectionner `Montant` → Type → Nombre décimal.
3. Sélectionner `DateVente` → Type → Date.
4. Supprimer les doublons sur `IDVente`.
5. Appliquer `Format → Supprimer les espaces` sur `Produit`.
6. Remplacer les valeurs nulles de `Quantite` par zéro uniquement si cette règle est validée par le métier.
7. Renommer les étapes importantes dans le volet **Étapes appliquées**.
8. **Fermer et appliquer**.

### Exemple SQL

Une sélection limitée à la source peut réduire les données transférées :

```SQL
SELECT DateVente, IDProduit, IDClient, Montant
FROM dbo.Ventes
WHERE DateVente >= '2026-01-01';
```

Ne sélectionnez pas `*` par habitude. Importer uniquement les colonnes utiles simplifie le modèle.

### Exemple M

```powerquery
Table.Propre = Table.TransformColumns(
    Source,
    {{"Produit", Text.Trim, type text}}
)
```

`Table.TransformColumns` reçoit une table, la colonne à modifier, la fonction `Text.Trim` puis le type attendu. Il n’est pas nécessaire de devenir programmeur : savoir lire les fonctions générées aide à diagnostiquer une erreur.

### Capture à insérer

L’éditeur Power Query avec l’aperçu central et le volet **Étapes appliquées** affichant `Source`, `Type modifié`, `Doublons supprimés` et `Texte nettoyé`.

## Erreurs fréquentes

- Corriger manuellement le fichier source au lieu de rendre la transformation reproductible.
- Changer les types après des calculs qui dépendent déjà de ces types.
- Utiliser Fusionner pour empiler des mois, ou Ajouter pour enrichir une ligne.

## Bonnes pratiques

Renommer les requêtes, désactiver le chargement des requêtes intermédiaires, conserver une étape par intention et documenter les hypothèses de nettoyage.

## Exercices

**Guidé :** normalisez une colonne Ville contenant `Paris`, `paris` et `Paris ` ; remplacez les vides de Quantité et contrôlez le nombre de lignes.

**Autonome :** combinez trois fichiers mensuels, extraire le mois du nom de fichier et comparez le total avant / après.

**Correction :** utiliser Ajouter pour empiler les fichiers ; contrôler les types et conserver une colonne Mois ; écrire dans une note le total attendu et le total obtenu.

## Mini-projet

Créez un pipeline de qualité sur une table volontairement imparfaite : dates mixtes, espaces, doublons, nulls et erreurs. Livrez la requête propre et la liste des règles.

---

# Chapitre 4 — Relations et modèle en étoile

## Objectifs

Distinguer faits et dimensions, définir la granularité, créer une relation `1:*` et éviter les chemins ambigus.

## Prérequis

Plusieurs tables propres et une clé d’identification.

## Notions fondamentales

La **table de faits** contient les événements mesurables. La **dimension** décrit ces événements. Dans un modèle en étoile, la table de faits est au centre et les dimensions sont autour.

Une relation `1:*` signifie qu’une ligne unique de la dimension correspond à plusieurs lignes dans le fait. Par exemple, un produit peut apparaître dans de nombreuses ventes, mais une vente référence un seul produit.

## Démonstration

1. Ouvrir la vue Modèle.
2. Relier `D_Produit[IDProduit]` à `F_Ventes[IDProduit]`.
3. Vérifier Cardinalité : **Un à plusieurs (1:*)**.
4. Vérifier Direction de filtrage : **Unique**, de la dimension vers le fait.
5. Relier `D_Date[Date]` à `F_Ventes[DateVente]`.
6. Créer une table calendrier si nécessaire et la marquer comme table de dates.
7. Tester : le segment `Categorie` doit modifier `Total Ventes`.

### Table calendrier

```DAX
D_Date = CALENDAR(DATE(2025,1,1), DATE(2026,12,31))
```

On ajoute ensuite des colonnes d’année, de mois, de trimestre et de numéro de mois. Triez le nom du mois par `NumMois` pour éviter l’ordre alphabétique.

### Capture à insérer

La vue Modèle avec `F_Ventes` au centre, reliée à `D_Date`, `D_Produit`, `D_Client` et `D_Region`, chaque relation affichant `1` du côté dimension et `*` du côté fait.

## Erreurs fréquentes

- Relier deux tables sur une colonne non unique.
- Créer des relations bidirectionnelles partout.
- Mélanger les descriptions et les faits dans une table géante.
- Oublier d’indiquer la granularité d’une table.

## Bonnes pratiques

Préfixer `D_` et `F_`, masquer les clés techniques, conserver un modèle simple et utiliser une vraie dimension Date pour toutes les analyses temporelles.

## Exercices

**Guidé :** dessinez le modèle d’une école avec `F_Notes`, `D_Etudiant`, `D_Matiere`, `D_Classe` et `D_Date`.

**Autonome :** repérez les relations nécessaires dans un modèle d’achats : commandes, fournisseurs, articles, dates et entrepôts.

**Correction :** les dimensions sont du côté `1`, les événements du côté `*`; une commande peut contenir plusieurs lignes, un article peut figurer dans plusieurs lignes.

## Mini-projet

Livrez un modèle de ventes sans relation ambiguë, avec calendrier marqué et document de granularité des tables.

---

# Chapitre 5 — Mesures, colonnes calculées et agrégations DAX

## Objectifs

Choisir le bon objet de calcul, créer un socle de mesures et utiliser les fonctions d’agrégation.

## Prérequis

Un modèle en étoile correctement relié.

## Mesure ou colonne calculée ?

Une **mesure** est calculée à l’affichage selon les filtres ; elle est idéale pour un KPI. Une **colonne calculée** est évaluée ligne par ligne lors de l’actualisation ; elle sert à créer une catégorie stable. Une **table calculée** crée une table dans le modèle ; elle est utile pour des besoins ciblés de modélisation.

### Fonctions d’agrégation

| Fonction | Rôle | Exemple |
|---|---|---|
| `SUM` | Additionner une colonne numérique | `SUM(F_Ventes[Montant])` |
| `AVERAGE` | Moyenne des valeurs | `AVERAGE(F_Notes[Note])` |
| `MIN` / `MAX` | Plus petite / plus grande valeur | `MAX(F_Ventes[DateVente])` |
| `COUNT` | Compter des valeurs numériques | `COUNT(F_Ventes[IDCommande])` |
| `COUNTA` | Compter les valeurs non vides | `COUNTA(D_Client[Client])` |
| `DISTINCTCOUNT` | Compter les valeurs uniques | `DISTINCTCOUNT(F_Ventes[IDClient])` |
| `COUNTROWS` | Compter les lignes d’une table | `COUNTROWS(F_Ventes)` |

## Démonstration : créer un socle de KPI

Dans le volet Données, clic droit sur `F_Ventes` → **Nouvelle mesure** :

```DAX
Total Ventes = SUM(F_Ventes[Montant])
Quantité Totale = SUM(F_Ventes[Quantite])
Clients Uniques = DISTINCTCOUNT(F_Ventes[IDClient])
Commandes = DISTINCTCOUNT(F_Ventes[IDCommande])
Panier Moyen = DIVIDE([Total Ventes], [Commandes], 0)
```

Déposez les trois premières mesures dans des cartes. Filtrez par région et vérifiez que les résultats changent.

### Lire une formule

Dans `Clients Uniques = DISTINCTCOUNT(F_Ventes[IDClient])` : le nom est à gauche, la fonction indique l’opération et la référence entre crochets indique la colonne concernée. Une mesure doit être nommée comme un résultat métier, pas comme un détail technique.

### Capture à insérer

Le clic droit sur la table `F_Ventes`, le choix **Nouvelle mesure** et la barre de formule affichant `Total Ventes = SUM(...)`.

## Erreurs fréquentes

- Créer une colonne calculée pour un total global.
- Utiliser `COUNT` sur une colonne texte.
- Compter les lignes au lieu des clients uniques.
- Laisser Power BI choisir une agrégation sans la vérifier.

## Bonnes pratiques

Créer des mesures atomiques puis les réutiliser, formater les devises et pourcentages, classer les mesures dans un dossier d’affichage et masquer les colonnes techniques.

## Exercices

**Guidé :** créez Total Ventes, Panier Moyen, Clients Uniques et Produits Vendus. Testez-les par mois.

**Autonome :** avec `F_Notes`, créez Moyenne Générale, Note Max, Nombre d’Évaluations et Étudiants Uniques.

**Correction :** `AVERAGE(F_Notes[Note])`, `MAX(F_Notes[Note])`, `COUNTROWS(F_Notes)` et `DISTINCTCOUNT(F_Notes[IDEtudiant])`.

## Mini-projet

Construisez une page KPI commercial avec chiffre d’affaires, commandes, panier moyen, marge et clients uniques, accompagnés d’une table de contrôle par région.

---

# Chapitre 6 — DAX : logique, contexte, filtres et temps

## Objectifs

Comprendre le contexte de filtre, utiliser `CALCULATE`, `FILTER`, `ALL`, les fonctions logiques et les comparaisons temporelles.

## Prérequis

Chapitre 5 et table de dates continue et reliée.

## Le contexte de filtre

Une mesure ne calcule pas forcément tout le modèle. Dans une carte filtrée sur la région Nord et le mois de mars, elle s’évalue dans ce contexte. Le même calcul peut donc produire une valeur différente selon le visuel.

## Fonctions de filtrage

### `CALCULATE`

```DAX
Ventes Premium =
CALCULATE(
    [Total Ventes],
    D_Produit[Segment] = "Premium"
)
```

`CALCULATE` reçoit une expression puis ajoute ou modifie un contexte. C’est la fonction centrale de DAX pour les analyses conditionnelles.

### `FILTER`

```DAX
Ventes Positives =
CALCULATE(
    [Total Ventes],
    FILTER(F_Ventes, F_Ventes[Montant] > 0)
)
```

`FILTER` renvoie une table qui respecte une condition. Utilisez-le lorsque le filtre nécessite une logique plus détaillée.

### `ALL`

```DAX
Part du Total =
DIVIDE(
    [Total Ventes],
    CALCULATE([Total Ventes], ALL(D_Produit[Categorie])),
    0
)
```

`ALL` retire le filtre indiqué. Il est utile pour une part du total ou un rang, mais peut ignorer un filtre attendu.

## Fonctions logiques

```DAX
Statut =
SWITCH(
    TRUE(),
    [Variation %] > 0.1, "Dépassé",
    [Variation %] >= -0.1, "Stable",
    "À surveiller"
)
```

`IF` traite deux cas. `SWITCH` rend plusieurs cas plus lisibles. `AND` exige deux conditions vraies, `OR` une seule et `NOT` inverse une condition.

```DAX
Risque =
IF(
    AND([Marge %] < 0.1, [Variation %] < 0),
    "Oui",
    "Non"
)
```

## Analyse temporelle

```DAX
Ventes N-1 =
CALCULATE(
    [Total Ventes],
    DATEADD(D_Date[Date], -1, YEAR)
)

Variation % =
DIVIDE([Total Ventes] - [Ventes N-1], [Ventes N-1], 0)

Ventes Cumulées =
TOTALYTD([Total Ventes], D_Date[Date])
```

### Démonstration

1. Créer `Ventes N-1`.
2. Créer `Variation %`.
3. Placer Année et Mois sur un graphique.
4. Ajouter les deux mesures.
5. Ajouter une carte de variation et la formater en pourcentage.
6. Tester une année et un mois précis.

### Capture à insérer

La barre de formule avec autocomplétion sur `CALCULATE`, puis un visuel montrant les courbes N et N-1.

## Erreurs fréquentes

- Utiliser `ALL` sans mesurer l’effet sur les segments.
- Filtrer la table de faits alors qu’une dimension convient.
- Comparer des périodes de longueurs différentes.
- Construire des `IF` imbriqués impossibles à relire.

## Bonnes pratiques

Décomposer les calculs, tester chaque mesure dans une carte et un tableau, utiliser `DIVIDE`, et documenter le contexte attendu.

## Exercices

**Guidé :** créez la part du total par catégorie et vérifiez que les catégories totalisent 100 %.

**Autonome :** créez un statut `Fort`, `Stable` ou `À surveiller` avec `SWITCH(TRUE())`.

**Correction :** `SWITCH(TRUE(), [Variation %] > 0.1, "Fort", [Variation %] >= -0.1, "Stable", "À surveiller")`.

## Mini-projet

Livrez une page d’analyse temporelle avec N, N-1, variation, cumul annuel et alerte sur les régions sous -10 %.

---

# Chapitre 7 — Statistiques descriptives et choix des visuels

## Objectifs

Décrire une distribution, distinguer moyenne et médiane, choisir un visuel adapté et construire une page lisible.

## Prérequis

Mesures DAX fonctionnelles et données contrôlées.

## Statistiques descriptives

- **Effectif :** nombre d’observations.
- **Somme :** total des valeurs.
- **Moyenne :** total divisé par le nombre d’observations ; sensible aux valeurs extrêmes.
- **Médiane :** valeur qui sépare les observations en deux groupes ; plus robuste aux extrêmes.
- **Minimum / maximum :** bornes observées.
- **Étendue :** maximum moins minimum.
- **Écart-type :** dispersion autour de la moyenne.
- **Percentile :** seuil en dessous duquel se trouve une proportion d’observations.

Pour un délai de livraison, une moyenne de 9 jours peut cacher quelques commandes à 90 jours. La médiane et le percentile 90 complètent l’analyse.

### Formules utiles

```DAX
Moyenne Délai = AVERAGE(F_Commandes[DelaiJours])
Médiane Délai = MEDIAN(F_Commandes[DelaiJours])
Ecart Type = STDEV.P(F_Commandes[DelaiJours])
P90 Délai = PERCENTILEX.INC(F_Commandes, F_Commandes[DelaiJours], 0.9)
```

Toujours préciser l’unité et le périmètre : « médiane des délais livrés, commandes de 2026 ».

## Choisir un visuel

| Question | Visuel |
|---|---|
| Comment cela évolue ? | Courbe |
| Que compare-t-on ? | Barres triées |
| Quelle est la répartition ? | Histogramme ou boîte à moustaches |
| Où se situe l’écart ? | Carte, si les données géographiques sont fiables |
| Quel est le niveau actuel ? | Carte KPI avec cible |
| Quel détail faut-il vérifier ? | Tableau ou matrice |

Un camembert ne convient que pour quelques parts d’un même total. Les visuels 3D et les jauges décoratives sont généralement à éviter.

## Démonstration

1. Placer trois cartes : Total Ventes, Variation %, Marge %.
2. Ajouter une courbe des ventes par mois.
3. Ajouter des barres horizontales par région, triées décroissantes.
4. Ajouter un segment Année.
5. Utiliser une couleur neutre pour le contexte et une couleur d’accent pour l’alerte.
6. Rédiger des titres qui portent un message : « Le Nord accélère au T3 » plutôt que « Ventes ».

### Capture à insérer

Le volet Visualisations avec Axe X, Axe Y, Légende, Valeurs et le panneau Format ouvert sur les titres et étiquettes.

## Erreurs fréquentes

- Confondre moyenne et médiane.
- Mettre trop de visuels sur une page.
- Utiliser le rouge et le vert comme seules informations.
- Tronquer un axe et exagérer visuellement une variation.

## Bonnes pratiques

Limiter une page à une intention, aligner les objets, conserver trois couleurs principales, ajouter des unités et tester la lisibilité à 100 %.

## Exercices

**Guidé :** remplacez huit visuels redondants par cinq visuels hiérarchisés et reformulez leurs titres.

**Autonome :** pour un suivi de stock, choisissez cinq visuels et justifiez chacun.

**Correction indicative :** KPI stock critique, barres des produits à réapprovisionner, courbe de l’évolution, matrice par entrepôt et tableau de contrôle.

## Mini-projet

Refondez la page de votre premier rapport en une page « Vue dirigeant ». Ajoutez une annotation sur le fait le plus important.

---

# Chapitre 8 — Filtres, segments, drill-through et expérience utilisateur

## Objectifs

Configurer les interactions, créer une page de détail, organiser la navigation et prendre en compte l’accessibilité.

## Notions

- **Filtre de page :** s’applique à une page.
- **Filtre de rapport :** s’applique au rapport entier.
- **Segment :** filtre visible et manipulable par le lecteur.
- **Info-bulle :** détail au survol.
- **Drill-through :** passage vers une page détaillée en conservant un contexte.
- **Signet et bouton :** navigation ou état enregistré d’une page.

## Démonstration : détail Produit

1. Créer une page `Détail Produit`.
2. Déposer `D_Produit[NomProduit]` dans la zone Drill-through.
3. Ajouter une carte Total Ventes et un tableau de transactions.
4. Depuis la page d’analyse, clic droit sur un produit → Drill-through.
5. Ajouter un bouton Retour.
6. Utiliser **Format → Modifier les interactions** pour vérifier quels visuels filtrent ou surlignent les autres.

### Capture à insérer

Le ruban **Modifier les interactions** avec les icônes Filtrer, Surligner et Aucun au-dessus des visuels.

## Bonnes pratiques UX

Afficher la période et les filtres actifs, limiter les segments aux questions fréquentes, prévoir une navigation claire et des textes alternatifs. Un rapport doit fonctionner au clavier et conserver un contraste suffisant.

## Exercices

**Guidé :** ajoutez un segment Année, un segment Catégorie, une info-bulle avec Marge et un drill-through Client.

**Autonome :** concevez une navigation de trois pages avec boutons Accueil, Analyse et Détail.

**Correction :** chaque page doit pouvoir être quittée sans utiliser le bouton Retour du navigateur ; les filtres doivent agir uniquement sur les visuels attendus.

## Mini-projet

Dessinez le parcours d’un utilisateur depuis un KPI en alerte jusqu’à la transaction expliquant l’écart.

---

# Chapitre 9 — Power BI Service, publication et actualisation

## Objectifs

Publier, distinguer rapport / modèle sémantique / tableau de bord / application, configurer l’actualisation et partager avec méthode.

## Notions fondamentales

Desktop construit, Service diffuse. Un espace de travail est un environnement d’équipe avec des rôles et un cycle de publication. Une application regroupe du contenu validé destiné à des lecteurs.

Une actualisation relance les requêtes et recharge le modèle. Une source locale peut nécessiter une **passerelle**, tandis qu’une source cloud nécessite des identifiants et une fréquence correctement configurés.

## Démonstration

1. Enregistrer le `.pbix`.
2. Cliquer sur **Publier** et sélectionner l’espace de travail de test.
3. Ouvrir le rapport dans Service.
4. Comparer trois KPI avec Desktop.
5. Ouvrir les paramètres du modèle sémantique.
6. Vérifier les identifiants et l’historique d’actualisation.
7. Tester un rafraîchissement manuel.
8. Partager uniquement avec un utilisateur ou groupe autorisé.

### Capture à insérer

Le bouton **Publier** de Desktop, la sélection de l’espace de travail et le message de publication réussie dans Service.

## Erreurs fréquentes

- Partager « toute personne ayant le lien » sans validation.
- Publier dans un espace personnel un rapport destiné à une équipe.
- Ne pas tester l’actualisation après publication.

## Bonnes pratiques

Nommer l’espace, le rapport, le propriétaire et la fréquence ; ajouter une page À propos ; documenter la date et vérifier Service, pas seulement Desktop.

## Exercices

**Guidé :** publiez un rapport de test et rédigez sa fiche : propriétaire, URL, source, fréquence, résultat d’actualisation.

**Autonome :** définissez les rôles d’une équipe de 25 commerciaux : construction, validation, lecture et alerte.

**Correction indicative :** analystes contributeurs, responsable BI propriétaire, commerciaux lecteurs, direction validatrice, alerte au propriétaire et à l’administrateur.

## Mini-projet

Livrez une version en ligne contrôlée, un accès lecteur et une fiche de mise à disposition.

---

# Chapitre 10 — Sécurité et gouvernance

## Objectifs

Comprendre les droits, mettre en place une sécurité au niveau des lignes, documenter les données sensibles et construire une checklist de confiance.

## Sécurité au niveau des lignes

La **RLS** limite les lignes visibles selon l’utilisateur connecté. Un responsable régional peut voir sa région sans créer une copie du rapport.

Une table d’habilitation dynamique peut contenir `Email` et `Region`. Elle se relie au modèle et utilise l’identité de l’utilisateur :

```DAX
UtilisateurCourant = USERPRINCIPALNAME()
```

Pour un prototype, un rôle statique peut filtrer ainsi :

```DAX
D_Region[Region] = "Nord"
```

Dans Service, testez un compte lecteur réel. Un administrateur peut avoir un comportement différent et ne doit pas être votre seul test.

### Capture à insérer

**Modélisation → Gérer les rôles**, avec un rôle `Region_Nord` et l’expression de filtre visible.

## Gouvernance

La gouvernance couvre les droits, mais aussi le propriétaire, le glossaire, la qualité, la traçabilité, la durée de conservation et le cycle de revue.

### Checklist

- Source et fréquence visibles.
- KPI définis et validés.
- Droits minimaux nécessaires.
- Données personnelles minimisées ou protégées.
- Propriétaire identifié.
- Plan en cas d’échec d’actualisation.
- Revue des habilitations programmée.

## Erreurs fréquentes

- Tester la RLS avec un compte administrateur qui voit tout.
- Protéger le rapport sans protéger le fichier source.
- Oublier les changements de poste et les départs.

## Exercices

**Guidé :** créez la matrice d’accès d’un rapport RH pour direction, managers, RH et collaborateurs.

**Autonome :** concevez une RLS pour quatre régions avec deux responsables par région. Expliquez le risque d’un filtre codé en dur.

**Correction :** une table d’habilitations et `USERPRINCIPALNAME()` évitent de multiplier les rôles et permettent une gestion dynamique.

## Mini-projet

Réalisez l’audit de confiance de votre rapport et ajoutez une page Méthode avec source, date, définitions, limites et contact.

---

# Chapitre 11 — Projet guidé : cockpit commercial

## Brief

La direction veut comprendre pourquoi le chiffre d’affaires du dernier trimestre varie selon les régions. Elle attend une vue synthétique, une analyse par produit et un détail exportable.

## Livrables

- modèle en étoile documenté ;
- mesures `Total Ventes`, `Marge`, `Marge %`, `Clients Uniques`, `Ventes N-1`, `Variation %` ;
- page Vue dirigeant ;
- page Analyse produit ;
- page À propos ;
- note avec cinq contrôles de cohérence.

## Plan de livraison

1. **Cadrage :** définir chaque KPI.
2. **Données :** nettoyer et typer.
3. **Modèle :** relations et calendrier.
4. **Calculs :** mesures atomiques, puis indicateurs dérivés.
5. **Récit :** synthèse, analyse, détail et navigation.
6. **Contrôle :** chiffres, filtres, accessibilité, partage.

## Contrôles minimum

- total des ventes comparé à la source ;
- nombre de lignes avant / après nettoyage ;
- filtre d’une région vérifié manuellement ;
- période sans donnée testée ;
- valeur de N-1 contrôlée sur un mois connu.

## Exercice

Présentez le rapport en cinq minutes : problème, message principal, preuve, action recommandée et limites.

## Correction attendue

La présentation doit commencer par une conclusion et non par une description de chaque graphique. Exemple : « La région Sud décroche sur la catégorie X au T3 ». Montrez ensuite la preuve et proposez une action.

---

# Chapitre 12 — Projet final et portfolio

## Mission

Choisissez ventes, stocks, RH, éducation, finance, agriculture ou un projet d’activité personnelle. Le sujet importe moins que la qualité de la démarche.

## Grille d’évaluation

| Critère | Attendu | Poids |
|---|---|---:|
| Besoin et récit | Public et décisions explicites | 20 % |
| Données et modèle | Power Query et étoile fiables | 25 % |
| DAX et qualité | Mesures justes et contrôles | 25 % |
| Design et usage | Hiérarchie, interactions, accessibilité | 20 % |
| Gouvernance | Source, sécurité, actualisation, limites | 10 % |

## Checklist finale

1. Le besoin tient en une phrase.
2. Chaque relation et mesure a une raison d’être.
3. Les résultats ont été comparés à une source.
4. Les filtres ne créent pas de surprise.
5. La date de rafraîchissement est visible.
6. Le rapport peut être repris par quelqu’un d’autre.
7. Aucune donnée personnelle réelle n’est exposée dans le portfolio.

## Soutenance en sept minutes

- Minute 1 : contexte et décision.
- Minutes 2–3 : vue d’ensemble et message principal.
- Minutes 4–5 : exploration d’un écart.
- Minute 6 : modèle, mesure ou contrôle qui rend le résultat fiable.
- Minute 7 : recommandation, limites et prochaine étape.

## Mini-projet final

Publiez le dashboard, sa documentation et votre présentation. Ajoutez les captures au portfolio en anonymisant les données et en indiquant clairement ce qui est réel, simulé ou confidentiel.

---

# Annexe A — Référence DAX essentielle

```DAX
-- Agrégations
Total = SUM(F_Ventes[Montant])
Moyenne = AVERAGE(F_Ventes[Montant])
Minimum = MIN(F_Ventes[Montant])
Maximum = MAX(F_Ventes[Montant])
Valeurs = COUNT(F_Ventes[IDCommande])
NonVides = COUNTA(D_Client[Client])
Uniques = DISTINCTCOUNT(F_Ventes[IDClient])
Lignes = COUNTROWS(F_Ventes)

-- Logique
Alerte = IF([Stock] < [Seuil], "Réapprovisionner", "OK")
Statut = SWITCH(TRUE(), [Variation %] > .1, "Fort", [Variation %] >= -.1, "Stable", "Faible")
Test Composé = IF(AND([Marge %] < .1, [Variation %] < 0), "Risque", "Normal")

-- Filtres
Ventes Premium = CALCULATE([Total], D_Produit[Segment] = "Premium")
Ventes Positives = CALCULATE([Total], FILTER(F_Ventes, F_Ventes[Montant] > 0))
Part Total = DIVIDE([Total], CALCULATE([Total], ALL(D_Produit)), 0)

-- Temps
N-1 = CALCULATE([Total], DATEADD(D_Date[Date], -1, YEAR))
Cumul Annuel = TOTALYTD([Total], D_Date[Date])
```

### Règles de lecture

- Une mesure dynamique répond au contexte du visuel.
- `CALCULATE` modifie ce contexte.
- `FILTER` renvoie une table filtrée.
- `ALL` retire des filtres.
- `DIVIDE` est plus sûr que `/` lorsque zéro est possible.
- Les fonctions temporelles exigent une table Date continue et reliée.

# Annexe B — Checklist avant publication

- [ ] Le besoin, le public et la décision sont écrits.
- [ ] Les colonnes ont les bons types.
- [ ] Les doublons, valeurs nulles et erreurs sont traités.
- [ ] La granularité des faits est connue.
- [ ] Le modèle est en étoile.
- [ ] Les relations sont testées.
- [ ] Les mesures sont nommées et formatées.
- [ ] Les totaux ont été rapprochés d’une source.
- [ ] Les titres portent un message.
- [ ] Les unités, dates et filtres sont visibles.
- [ ] Le rapport est lisible au clavier et avec un contraste suffisant.
- [ ] La page À propos indique source, propriétaire et actualisation.
- [ ] Les rôles et accès ont été testés avec un compte lecteur.
- [ ] L’actualisation est planifiée et son échec est surveillé.

> Un dashboard professionnel n’est pas celui qui montre le plus de choses. C’est celui qui permet à la bonne personne de prendre une meilleure décision, avec confiance.
