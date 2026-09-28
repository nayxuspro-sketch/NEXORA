const modules = [
  {
    id: 1, title: 'Comprendre la Business Intelligence', short: 'Les données au service de la décision.', time: '35 min', lessons: 3, status: 'done', kicker: 'LES FONDAMENTAUX', subtitle: 'Avant de manipuler un outil, comprenons le problème qu’il résout.',
    objectives: ['Expliquer la différence entre donnée, information et décision.', 'Situer Power BI dans une démarche de Business Intelligence.', 'Identifier les grandes étapes d’un projet analytique.'],
    prereq: 'Aucun prérequis. Ce module s’adresse à vous si le mot « BI » est encore nouveau.',
    content: `<h2>Pourquoi parle-t-on de Business Intelligence ?</h2><p>Une entreprise produit chaque jour des données : commandes, factures, stocks, clients, absences ou résultats scolaires. La <strong>Business Intelligence (BI)</strong> est la démarche qui transforme ces traces en informations fiables, puis en décisions.</p><div class="definition-card"><div class="definition-icon">◈</div><div><strong>Business Intelligence</strong><p>Ensemble des méthodes et outils qui collectent, préparent, analysent et présentent des données pour aider une organisation à décider. Imaginez un tableau de bord de voiture : il ne remplace pas le conducteur, mais il lui montre la vitesse, le carburant et les alertes au bon moment.</p></div></div><h3>Donnée, information, décision : la chaîne de valeur</h3><table class="comparison-table"><thead><tr><th>NIVEAU</th><th>EXEMPLE VENTES</th><th>QUESTION POSÉE</th></tr></thead><tbody><tr><td>Donnée</td><td>120 unités, 48 000 €, 12/09/2026</td><td>Qu’a-t-on enregistré ?</td></tr><tr><td>Information</td><td>Le chiffre d’affaires progresse de 18 %</td><td>Que se passe-t-il ?</td></tr><tr><td>Décision</td><td>Renforcer le stock de la gamme A</td><td>Que fait-on maintenant ?</td></tr></tbody></table><h2>Le rôle de Power BI</h2><p>Power BI est une plateforme Microsoft composée de <strong>Power BI Desktop</strong> pour préparer et construire un rapport, de <strong>Power BI Service</strong> pour le publier et le partager, et d’applications mobiles pour le consulter. Desktop est votre atelier ; Service est la vitrine sécurisée de votre organisation.</p><div class="capture-placeholder"><span>▧</span><div><strong>Capture à insérer — vue d’ensemble</strong><p>Afficher un schéma montrant Sources → Power Query → Modèle → Rapport → Service. Ajouter une légende sous chaque étape.</p></div></div><h2>Le cycle d’un projet BI</h2><ol><li><strong>Comprendre le besoin :</strong> quelle décision doit être améliorée ?</li><li><strong>Collecter :</strong> où sont les fichiers et qui en est responsable ?</li><li><strong>Préparer :</strong> corriger les types, les doublons et les valeurs manquantes.</li><li><strong>Modéliser :</strong> relier les tables sans ambiguïté.</li><li><strong>Analyser et raconter :</strong> choisir les mesures et visuels adaptés.</li><li><strong>Publier et maintenir :</strong> sécuriser, actualiser, documenter.</li></ol><div class="tip-box"><strong>Réflexe professionnel :</strong> commencez toujours par la question métier, jamais par le graphique qui vous semble joli. Un indicateur sans décision associée est souvent un simple chiffre décoratif.</div>`,
    demo: { title: 'Lire un besoin comme un analyste', steps: ['Prenez la demande « Je veux un dashboard des ventes ».', 'Reformulez-la : « Quelles décisions le responsable commercial doit-il prendre chaque lundi ? »', 'Listez trois questions : quelle région décroche ? quels produits accélèrent ? où le stock risque-t-il de manquer ?', 'Associez chaque question à un indicateur et à une fréquence de mise à jour.'], result: 'Vous obtenez un cahier des charges testable, au lieu d’un assemblage de graphiques.' },
    formula: { name: 'Indicateur de variation', code: 'Variation % = DIVIDE([Ventes N] - [Ventes N-1], [Ventes N-1])', explanation: 'On compare deux mesures puis on divise l’écart par la valeur de référence. DIVIDE évite une erreur si le dénominateur vaut zéro.' },
    errors: ['Confondre un tableau de données avec un tableau de bord : le premier détaille, le second aide à surveiller et décider.', 'Mesurer tout ce qui est disponible sans hiérarchiser les indicateurs.', 'Ignorer la qualité et la définition des données sources.'],
    best: ['Faire valider le vocabulaire métier : « client actif » doit avoir une définition écrite.', 'Limiter la page principale à quelques indicateurs prioritaires.', 'Conserver la source, la date d’actualisation et le propriétaire du rapport.'],
    guided: 'À partir d’une activité de votre choix (école, association ou entreprise), écrivez 3 décisions, 3 questions d’analyse et 1 indicateur pour chaque question.',
    autonomous: 'Un directeur d’école demande « un rapport des élèves ». Proposez une page de pilotage avec 4 indicateurs et expliquez la décision associée à chacun.',
    correction: 'Exemple : taux d’assiduité → contacter les élèves à risque ; effectif par niveau → anticiper les classes ; moyenne par matière → organiser le soutien ; évolution des inscriptions → ajuster la communication.',
    project: 'Fiche de cadrage BI : rédigez le besoin, le public, les décisions, les sources, la fréquence et les règles de confidentialité de votre futur projet.'
  },
  {
    id: 2, title: 'Vos premiers pas dans Power BI Desktop', short: 'Importer un fichier et créer son premier visuel.', time: '45 min', lessons: 3, status: 'current', kicker: 'PRISE EN MAIN', subtitle: 'Découvrez l’interface et réalisez votre premier rapport sans écrire une ligne de code.',
    objectives: ['Installer Power BI Desktop et repérer les vues principales.', 'Importer un fichier Excel ou CSV.', 'Créer, mettre en forme et enregistrer un premier visuel.'], prereq: 'Avoir un ordinateur Windows et le fichier Contoso fourni dans les ressources. Aucun prérequis Power BI.',
    content: `<h2>Desktop, votre atelier de construction</h2><p>Power BI Desktop est l’application installée sur votre ordinateur. Elle rassemble trois espaces : la <strong>vue Rapport</strong> pour raconter les données, la <strong>vue Données</strong> pour les inspecter et la <strong>vue Modèle</strong> pour voir les relations entre tables.</p><div class="definition-card"><div class="definition-icon">▦</div><div><strong>Un rapport n’est pas un fichier Excel décoré</strong><p>Excel travaille souvent feuille par feuille. Power BI construit un modèle réutilisable : une modification de filtre peut recalculer plusieurs visuels qui partagent les mêmes tables.</p></div></div><h3>Installation et configuration</h3><ol><li>Téléchargez Power BI Desktop depuis le site officiel Microsoft Store ou Microsoft Learn.</li><li>Ouvrez l’application, connectez-vous avec votre compte professionnel si votre organisation le demande.</li><li>Dans <strong>Fichier → Options et paramètres → Options</strong>, vérifiez la langue, le séparateur décimal et les préférences d’accessibilité.</li></ol><div class="capture-placeholder"><span>▧</span><div><strong>Capture à insérer — interface Desktop</strong><p>Montrer la barre de ruban, les icônes Rapport/Données/Modèle à gauche, le canevas central, les volets Données, Visualisations et Filtres à droite.</p></div></div><h2>Importer un fichier Excel</h2><p>Le connecteur décrit la porte d’entrée vers une source. Pour Excel : <strong>Accueil → Obtenir les données → Excel</strong>, choisissez le fichier, sélectionnez la feuille ou la table dans le navigateur, puis cliquez sur <strong>Transformer les données</strong> si un nettoyage est nécessaire ou sur <strong>Charger</strong> pour continuer.</p>`,
    demo: { title: 'Importer Contoso et créer un histogramme', steps: ['Accueil → Obtenir les données → Excel → sélectionner Contoso.xlsx.', 'Dans le navigateur, cocher la table Ventes puis cliquer sur Charger.', 'Dans le volet Données, faire glisser Catégorie vers l’axe X et Montant vers Valeurs.', 'Dans Format du visuel, donner le titre « Chiffre d’affaires par catégorie » et activer les étiquettes.', 'Enregistrer sous Contoso_Premier_Rapport.pbix.'], result: 'Un histogramme apparaît. Survolez une barre : l’infobulle doit afficher le montant correspondant à la catégorie.' },
    formula: { name: 'Premier total', code: 'Total Ventes = SUM(Ventes[Montant])', explanation: 'SUM additionne une colonne numérique. Le nom à gauche devient une mesure réutilisable dans tous les visuels.' },
    errors: ['Charger une feuille Excel désordonnée sans vérifier les en-têtes.', 'Déposer une colonne texte dans une zone de valeurs et obtenir un comptage au lieu d’une somme.', 'Oublier d’enregistrer le fichier .pbix, qui contient le modèle et le rapport.'],
    best: ['Donner aux tables et colonnes des noms lisibles dès l’import.', 'Masquer les colonnes techniques inutiles dans le volet Données.', 'Vérifier l’agrégation proposée : Somme, Moyenne, Nombre ou Ne pas résumer.'],
    guided: 'Importez la table Ventes, créez une carte avec Total Ventes et un histogramme par Région. Ajoutez un titre et vérifiez les montants avec une somme faite dans Excel.',
    autonomous: 'Importez votre propre CSV de dépenses. Créez une carte du total, un graphique par catégorie et un tableau des 10 lignes les plus récentes.',
    correction: 'La carte doit utiliser une mesure ou une somme de Montant. Le graphique doit utiliser Catégorie en axe et Montant en valeurs. Les types de données de Date et Montant doivent être respectivement Date et Nombre décimal.',
    project: 'Mini-rapport « Première lecture » : une page avec 3 cartes KPI, 2 visuels et un titre indiquant la période couverte. Prenez une capture de votre page pour votre carnet.'
  },
  {
    id: 3, title: 'Nettoyer avec Power Query', short: 'Transformer les données avant de les analyser.', time: '1 h 10', lessons: 4, status: 'locked', kicker: 'POWER QUERY', subtitle: 'Faites de la qualité de vos données un avantage, pas un obstacle.',
    objectives: ['Comprendre l’éditeur Power Query et les étapes appliquées.', 'Corriger types, valeurs nulles, doublons et colonnes inutiles.', 'Fusionner ou ajouter des requêtes avec méthode.'], prereq: 'Modules 1 et 2. Vous savez importer un fichier et repérer le volet Données.',
    content: `<h2>Power Query : l’atelier de préparation</h2><p>Power Query est le moteur de connexion et de transformation de Power BI. Il travaille <strong>avant</strong> le modèle : on y nettoie une donnée une fois pour que tous les visuels profitent d’une base propre. Chaque action devient une étape mémorisée, rejouable à la prochaine actualisation.</p><div class="definition-card"><div class="definition-icon">✧</div><div><strong>Une requête</strong><p>C’est une recette qui décrit comment passer de la source à une table prête à l’emploi. Comme une recette de cuisine, elle garde l’ordre des étapes et peut être rejouée avec de nouveaux ingrédients.</p></div></div><h3>Les transformations essentielles</h3><ul><li><strong>Type de données :</strong> texte, entier, décimal, date, date/heure, booléen.</li><li><strong>Valeurs :</strong> remplacer null, supprimer les erreurs, normaliser la casse et les espaces.</li><li><strong>Structure :</strong> promouvoir les en-têtes, dépivoter, fractionner ou fusionner des colonnes.</li><li><strong>Combinaisons :</strong> Ajouter des requêtes empile des lignes ; Fusionner des requêtes rapproche des colonnes grâce à une clé.</li></ul><div class="capture-placeholder"><span>▧</span><div><strong>Capture à insérer — éditeur Power Query</strong><p>Afficher le ruban Accueil, l’aperçu de table au centre et le volet Étapes appliquées à droite, avec une étape « Type modifié » sélectionnée.</p></div></div><h2>Le langage M, sans peur</h2><p>Chaque clic produit du code dans le langage M. Vous n’avez pas besoin de le mémoriser : l’interface génère la majorité des expressions. Lire la barre de formule vous aide simplement à comprendre l’ordre des opérations et à diagnostiquer une erreur.</p><h2>Excel, SQL et les autres sources</h2><p>Excel est pratique pour un premier prototype : privilégiez des <strong>tables nommées</strong> plutôt que des plages libres. Une base SQL est préférable pour un volume important ou une source partagée : avec <strong>Accueil → Obtenir les données → SQL Server</strong>, choisissez Importer pour travailler dans le modèle ou DirectQuery si la fraîcheur et la taille justifient une requête à la demande.</p><div class="formula-box"><div class="formula-label">EXEMPLE DE REQUÊTE SQL — À ADAPTER</div><code>SELECT DateVente, IDProduit, Montant<br>FROM dbo.Ventes<br>WHERE DateVente &gt;= '2026-01-01';</code><p><strong>Rôle :</strong> sélectionner les colonnes utiles et limiter les lignes dès la source. Ne sélectionnez pas « * » par habitude : moins de données transférées signifie souvent un modèle plus clair.</p></div><p>Le même principe s’applique aux fichiers CSV, dossiers, SharePoint, API ou services cloud : identifiez le propriétaire, la fréquence, les identifiants et la stratégie d’actualisation avant de construire les visuels.</p>`,
    demo: { title: 'Nettoyer la table Ventes', steps: ['Accueil → Transformer les données.', 'Sélectionner Montant → Type de données → Nombre décimal.', 'Sélectionner DateVente → Date.', 'Accueil → Supprimer les lignes → Supprimer les doublons sur IDVente.', 'Sélectionner Produit → Format → Supprimer les espaces superflus.', 'Fermer et appliquer, puis vérifier le nombre de lignes dans la vue Données.'], result: 'La table est fiable et la requête conserve toutes les transformations. À la prochaine actualisation, la recette sera rejouée.' },
    formula: { name: 'Exemple de M lisible', code: 'Table.Propre = Table.TransformColumns(Source, {{"Produit", Text.Trim, type text}})', explanation: 'Table.TransformColumns prend la table Source, applique Text.Trim à la colonne Produit et conserve le type texte.' },
    errors: ['Modifier directement le fichier source au lieu de documenter la transformation dans Power Query.', 'Changer un type trop tard, après des calculs qui ont déjà produit des erreurs.', 'Utiliser Fusionner alors qu’il fallait Ajouter, ou inversement.'],
    best: ['Renommer les requêtes et les étapes importantes.', 'Désactiver le chargement des requêtes intermédiaires qui ne servent qu’à une fusion.', 'Préférer une transformation reproductible à une correction manuelle ponctuelle.'],
    guided: 'Sur une table contenant « Paris », « paris » et « Paris  », normalisez la colonne Ville. Puis remplacez les cellules vides de Quantité par 0 et documentez chaque étape.',
    autonomous: 'Combinez trois fichiers mensuels de ventes qui ont les mêmes colonnes. Ajoutez une colonne Mois à partir du nom du fichier et contrôlez le total par mois.',
    correction: 'Les trois fichiers doivent être empilés avec Ajouter des requêtes. La colonne Mois peut être extraite du nom de fichier dans une requête depuis un dossier. Un contrôle de lignes et de total avant/après doit être écrit dans une note.',
    project: 'Pipeline de qualité : préparez une table source volontairement imparfaite (dates mixtes, espaces, doublons, valeurs nulles), puis livrez une requête propre et une liste des règles appliquées.'
  },
  {
    id: 4, title: 'Construire un modèle en étoile', short: 'Relier les tables sans créer de confusion.', time: '1 h 20', lessons: 4, status: 'locked', kicker: 'MODÉLISATION', subtitle: 'Un modèle solide rend les analyses simples, rapides et fiables.',
    objectives: ['Distinguer table de faits et table de dimensions.', 'Créer une relation 1-* avec la bonne direction de filtre.', 'Construire un modèle en étoile et éviter les ambiguïtés.'], prereq: 'Savoir importer et nettoyer plusieurs tables (modules 2 et 3).',
    content: `<h2>Penser en tables qui se complètent</h2><p>La <strong>table de faits</strong> contient les événements mesurables : une ligne de vente, un paiement, une absence. Une <strong>table de dimension</strong> décrit ces événements : client, produit, date, magasin. La dimension répond à « qui, quoi, quand, où » ; le fait répond à « combien ».</p><div class="definition-card"><div class="definition-icon">✣</div><div><strong>Le modèle en étoile</strong><p>Une table de faits au centre et des dimensions autour, comme les rayons d’une étoile. Cette organisation évite de répéter les descriptions dans chaque ligne de vente et rend les filtres prévisibles.</p></div></div><table class="comparison-table"><thead><tr><th>TABLE</th><th>CONTENU</th><th>EXEMPLES DE COLONNES</th></tr></thead><tbody><tr><td>F_Ventes</td><td>Une ligne par transaction</td><td>IDProduit, IDClient, Date, Quantité, Montant</td></tr><tr><td>D_Produit</td><td>Une ligne par produit</td><td>IDProduit, Nom, Catégorie, Marque</td></tr><tr><td>D_Date</td><td>Une ligne par jour</td><td>Date, Année, Mois, Trimestre</td></tr></tbody></table><div class="capture-placeholder"><span>▧</span><div><strong>Capture à insérer — vue Modèle</strong><p>Montrer F_Ventes au centre reliée à D_Date, D_Produit et D_Client par des relations 1 à plusieurs, filtre à sens unique.</p></div></div><h2>Les relations</h2><p>Une relation indique comment une valeur d’une table correspond à une valeur d’une autre. Dans Power BI, la relation habituelle est <strong>un-à-plusieurs (1:*)</strong> : une ligne de D_Produit filtre plusieurs lignes de F_Ventes. La clé du côté « 1 » doit être unique.</p>`,
    demo: { title: 'Relier Ventes, Produits et Calendrier', steps: ['Dans la vue Modèle, faites glisser D_Produit[IDProduit] vers F_Ventes[IDProduit].', 'Vérifiez Cardinalité : Un à plusieurs (1:*), côté 1 sur D_Produit.', 'Vérifiez Direction de filtrage : Unique, de la dimension vers le fait.', 'Créez la relation D_Date[Date] → F_Ventes[DateVente].', 'Testez : un segment Catégorie doit maintenant filtrer un total de ventes.'], result: 'Si le total change quand vous sélectionnez une catégorie, le filtre circule correctement de la dimension vers la table de faits.' },
    formula: { name: 'Clé de calendrier', code: 'D_Date = CALENDAR(DATE(2025,1,1), DATE(2026,12,31))', explanation: 'CALENDAR génère une ligne par date entre les deux bornes. On enrichit ensuite cette table avec Année, Mois et NumMois.' },
    errors: ['Relier deux tables sur une colonne non unique.', 'Mettre des colonnes de description dans la table de faits et créer un modèle géant.', 'Utiliser des relations bidirectionnelles partout et obtenir des chemins de filtre ambigus.'],
    best: ['Préfixer les tables avec D_ et F_ pour rendre leur rôle visible.', 'Marquer la table D_Date comme table de dates.', 'Masquer les clés techniques et afficher les colonnes métier utiles.'],
    guided: 'Dessinez sur papier le modèle de votre activité : un fait central et au moins trois dimensions. Indiquez la granularité exacte d’une ligne du fait.',
    autonomous: 'Construisez le modèle d’un établissement scolaire avec F_Notes, D_Etudiant, D_Matiere, D_Classe et D_Date. Déterminez les cardinalités.',
    correction: 'F_Notes contient une ligne par note attribuée. Les dimensions D_Etudiant, D_Matiere, D_Classe et D_Date sont du côté 1. Un étudiant peut avoir plusieurs notes, mais une note référence un seul étudiant.',
    project: 'Modèle de ventes : livrez une vue Modèle sans relation inactive ou ambiguë, documentez la granularité de F_Ventes et ajoutez une table calendrier complète.'
  },
  {
    id: 5, title: 'DAX : mesures et agrégations', short: 'Calculer ce qui compte vraiment.', time: '1 h 25', lessons: 5, status: 'locked', kicker: 'DAX · NIVEAU 1', subtitle: 'Passez d’une simple somme à des indicateurs métier réutilisables.',
    objectives: ['Différencier mesure, colonne calculée et table calculée.', 'Écrire les fonctions d’agrégation principales.', 'Comprendre la différence entre contexte de ligne et contexte de filtre.'], prereq: 'Avoir un modèle en étoile avec F_Ventes reliée à ses dimensions.',
    content: `<h2>Trois façons de calculer dans Power BI</h2><p>Une <strong>mesure</strong> est calculée à la demande selon les filtres du visuel : elle est idéale pour les KPI. Une <strong>colonne calculée</strong> est calculée ligne par ligne lors de l’actualisation : utile pour une catégorie stable. Une <strong>table calculée</strong> crée une nouvelle table dans le modèle : à réserver à des besoins de modélisation ciblés.</p><table class="comparison-table"><thead><tr><th>OBJET</th><th>QUAND LE CALCUL A LIEU</th><th>CAS D’USAGE</th></tr></thead><tbody><tr><td>Mesure</td><td>À l’affichage, selon les filtres</td><td>Total, marge, taux, KPI</td></tr><tr><td>Colonne calculée</td><td>À l’actualisation, pour chaque ligne</td><td>Segment, libellé, délai</td></tr><tr><td>Table calculée</td><td>À l’actualisation</td><td>Calendrier ou table intermédiaire</td></tr></tbody></table><h2>Les agrégations DAX</h2><p>Les fonctions <strong>SUM, AVERAGE, MIN, MAX, COUNT, COUNTA</strong> et <strong>DISTINCTCOUNT</strong> résument une colonne. La bonne fonction dépend de ce que représente la ligne et de la nature de la colonne.</p><div class="capture-placeholder"><span>▧</span><div><strong>Capture à insérer — nouvelle mesure</strong><p>Afficher le clic droit sur F_Ventes dans le volet Données, puis « Nouvelle mesure », avec la barre de formule active.</p></div></div><h3>Lire une formule mot à mot</h3>`,
    demo: { title: 'Créer un socle de mesures', steps: ['Clic droit sur F_Ventes → Nouvelle mesure.', 'Saisir Total Ventes = SUM(F_Ventes[Montant]). Valider avec Entrée.', 'Créer Quantité Totale = SUM(F_Ventes[Quantité]).', 'Créer Clients Uniques = DISTINCTCOUNT(F_Ventes[IDClient]).', 'Ajouter ces mesures dans trois cartes et filtrer par région pour tester leur réactivité.'], result: 'Les cartes se recalculent selon le contexte : un filtre Région Nord doit afficher uniquement les ventes et clients du Nord.' },
    formula: { name: 'Mesure fondamentale', code: 'Total Ventes = SUM(F_Ventes[Montant])', explanation: 'Total Ventes est le nom de la mesure. SUM est la fonction. F_Ventes[Montant] est la colonne numérique additionnée. Les crochets identifient une colonne.' },
    errors: ['Créer une colonne calculée pour un total global : elle répète le même total sur chaque ligne.', 'Utiliser COUNT sur Montant : COUNT compte les valeurs numériques, il ne les additionne pas.', 'Compter les lignes au lieu des clients uniques et surévaluer la clientèle.'],
    best: ['Créer une mesure plutôt que déposer directement une colonne dans un visuel.', 'Utiliser des noms explicites et des dossiers d’affichage pour classer les mesures.', 'Formater les devises, pourcentages et décimales dans les outils de mesure.'],
    guided: 'Créez Total Ventes, Panier Moyen = DIVIDE([Total Ventes], [Nombre Commandes]) et Produits Vendus. Testez les résultats par mois.',
    autonomous: 'À partir de F_Notes, créez Moyenne Générale, Note Max, Nombre d’Évaluations et Étudiants Uniques. Choisissez le bon agrégateur pour chaque besoin.',
    correction: 'Moyenne Générale = AVERAGE(F_Notes[Note]); Note Max = MAX(F_Notes[Note]); Nombre d’Évaluations = COUNTROWS(F_Notes); Étudiants Uniques = DISTINCTCOUNT(F_Notes[IDEtudiant]).',
    project: 'KPI commercial : une page avec CA, commandes, panier moyen, clients uniques et une table de contrôle qui affiche les mêmes mesures par région.'
  },
  {
    id: 6, title: 'DAX : contexte, filtres et temps', short: 'Comparer, filtrer et raconter une évolution.', time: '1 h 40', lessons: 6, status: 'locked', kicker: 'DAX · NIVEAU 2', subtitle: 'Maîtrisez CALCULATE et les fonctions qui font de DAX un langage d’analyse.',
    objectives: ['Expliquer le contexte de filtre avec des mots simples.', 'Utiliser CALCULATE, FILTER, ALL et les fonctions logiques.', 'Créer des comparaisons temporelles et des variations.'], prereq: 'Module 5 terminé, table D_Date marquée comme table de dates.',
    content: `<h2>Le contexte : la question invisible du calcul</h2><p>Quand une mesure apparaît dans une carte filtrée sur « Nord » et « Mars », Power BI ne calcule pas tout le modèle : il calcule dans ce <strong>contexte de filtre</strong>. DAX est puissant parce qu’une mesure sait répondre différemment selon la ligne, le segment ou la page qui la contient.</p><div class="definition-card"><div class="definition-icon">ƒx</div><div><strong>CALCULATE</strong><p>CALCULATE évalue une expression dans un contexte de filtre modifié. Imaginez une question posée avec une contrainte supplémentaire : « Quel est le CA, mais seulement pour la catégorie Audio ? »</p></div></div><h3>Les fonctions à connaître</h3><ul><li><strong>CALCULATE :</strong> modifier le contexte d’une mesure.</li><li><strong>FILTER :</strong> produire une table filtrée selon une expression.</li><li><strong>ALL :</strong> ignorer un ou plusieurs filtres.</li><li><strong>IF, SWITCH, AND, OR, NOT :</strong> créer une logique lisible.</li><li><strong>DATEADD, TOTALYTD :</strong> analyser la période et le cumul.</li></ul><div class="capture-placeholder"><span>▧</span><div><strong>Capture à insérer — formule DAX</strong><p>Afficher la barre de formule avec CALCULATE, la coloration syntaxique et la liste d’autocomplétion ouverte.</p></div></div><h2>Syntaxe guidée</h2>`,
    demo: { title: 'Créer une variation annuelle', steps: ['Créer Ventes N-1 = CALCULATE([Total Ventes], DATEADD(D_Date[Date], -1, YEAR)).', 'Créer Variation % = DIVIDE([Total Ventes] - [Ventes N-1], [Ventes N-1]).', 'Ajouter Année et Mois sur un graphique avec les deux mesures.', 'Ajouter une carte Variation % et formater en pourcentage.', 'Filtrer une année : la valeur N-1 doit se recalculer sur la période précédente.'], result: 'La courbe montre les ventes de l’année sélectionnée et de l’année précédente. Une variation positive est affichée en hausse.' },
    formula: { name: 'Filtrer une mesure', code: 'Ventes Premium = CALCULATE([Total Ventes], D_Produit[Segment] = "Premium")', explanation: 'CALCULATE prend l’expression [Total Ventes] puis ajoute le filtre Segment = Premium. Le résultat reste une mesure dynamique.' },
    errors: ['Utiliser ALL sans comprendre que les filtres de la page seront ignorés.', 'Filtrer une colonne de la table de faits alors qu’une dimension est disponible.', 'Comparer des périodes de longueurs différentes ou oublier une vraie table de dates.', 'Écrire un IF imbriqué illisible alors que SWITCH est plus clair.'],
    best: ['Décomposer une mesure complexe en petites mesures nommées.', 'Tester chaque mesure dans une carte puis dans un tableau avec plusieurs niveaux.', 'Utiliser DIVIDE(numérateur, dénominateur, 0) plutôt que le symbole / quand zéro est possible.'],
    guided: 'Créez Part du total = DIVIDE([Total Ventes], CALCULATE([Total Ventes], ALL(D_Produit[Catégorie]))) et vérifiez que la somme des catégories vaut 100 %.',
    autonomous: 'Créez un KPI « Statut » avec SWITCH : « Dépassé » si la variation > 10 %, « Stable » entre -10 % et 10 %, « À surveiller » sinon.',
    correction: 'Statut = SWITCH(TRUE(), [Variation %] > 0.1, "Dépassé", [Variation %] >= -0.1, "Stable", "À surveiller"). SWITCH(TRUE()) évalue les conditions dans l’ordre.',
    project: 'Analyse temporelle : une page qui compare N/N-1, affiche un cumul annuel et signale les régions dont la variation est inférieure à -10 %. Documentez chaque mesure.'
  },
  {
    id: 7, title: 'Choisir les bons visuels', short: 'Faire parler les chiffres sans les déformer.', time: '55 min', lessons: 4, status: 'locked', kicker: 'DATAVIZ', subtitle: 'La forme d’un graphique doit servir la question, pas l’inverse.',
    objectives: ['Décrire une distribution avec moyenne, médiane et percentile.', 'Associer une question analytique à un visuel.', 'Construire une page lisible avec hiérarchie visuelle.'], prereq: 'Modules 2 à 6. Vous savez créer des mesures et les filtrer.',
    content: `<h2>Le visuel est une phrase</h2><p>Un visuel répond à une intention. Une courbe raconte une évolution, des barres comparent des catégories, une carte localise, une carte KPI attire l’œil sur une valeur. Si vous devez expliquer le graphique avant qu’il soit compris, le choix ou le titre est à revoir.</p><h3>Un peu de statistique descriptive</h3><p>La moyenne est sensible aux valeurs extrêmes ; la médiane décrit la valeur centrale ; l’écart-type mesure la dispersion. Pour un délai de livraison, ajoutez un percentile 90 afin de savoir dans quel délai 90 % des commandes sont livrées.</p><div class="formula-box"><div class="formula-label">MESURES STATISTIQUES</div><code>Médiane Délai = MEDIAN(F_Commandes[DelaiJours])<br>P90 Délai = PERCENTILEX.INC(F_Commandes, F_Commandes[DelaiJours], 0.9)</code><p>Interprétez toujours l’unité, le périmètre et la période : « médiane des délais livrés, commandes de 2026 ».</p></div><table class="comparison-table"><thead><tr><th>QUESTION</th><th>VISUEL RECOMMANDÉ</th><th>À ÉVITER</th></tr></thead><tbody><tr><td>Comment évolue le CA ?</td><td>Courbe avec axe temporel</td><td>Camembert par mois</td></tr><tr><td>Quelle région compare-t-on ?</td><td>Barres horizontales triées</td><td>Radar ou 3D</td></tr><tr><td>Où sont les écarts géographiques ?</td><td>Carte si la géographie est fiable</td><td>Carte si les codes sont ambigus</td></tr><tr><td>Quel est le niveau actuel ?</td><td>Carte KPI avec cible</td><td>Jauge décorative sans contexte</td></tr></tbody></table><div class="capture-placeholder"><span>▧</span><div><strong>Capture à insérer — volet Visualisations</strong><p>Montrer le choix entre Axe X, Axe Y, Légende, Valeurs et le panneau Format avec les titres et étiquettes activés.</p></div></div><h2>Couleur et attention</h2><p>Utilisez une couleur neutre pour le contexte et une couleur d’accent pour l’alerte ou le résultat important. Ne donnez pas une couleur différente à chaque catégorie sans raison : le lecteur devra mémoriser une légende inutile.</p>`,
    demo: { title: 'Construire une page de suivi', steps: ['Placer trois cartes en haut : Total Ventes, Variation %, Marge.', 'Ajouter une courbe CA par mois au centre gauche.', 'Ajouter des barres horizontales CA par région au centre droit.', 'Ajouter un segment Année et un segment Région.', 'Aligner les objets, donner un titre à la page et vérifier la lecture en 100 %.'], result: 'La page répond rapidement à trois questions : combien, comment cela évolue et où agir.' },
    formula: { name: 'Mesure pour une cible', code: 'Écart Objectif = [Total Ventes] - [Objectif Ventes]', explanation: 'Une mesure d’écart est souvent plus utile qu’une valeur seule : elle indique la distance à l’objectif et alimente la couleur conditionnelle.' },
    errors: ['Surcharger la page avec trop de visuels.', 'Utiliser le rouge et le vert comme seules informations : penser aux personnes daltoniennes.', 'Afficher des décimales inutiles ou des axes tronqués qui dramatisent un écart.'],
    best: ['Commencer par une grille et aligner les bords.', 'Écrire des titres qui donnent le message : « Le Nord accélère au T3 » est plus utile que « Ventes ».', 'Tester le rapport avec un collègue qui ne connaît pas les données.'],
    guided: 'Prenez une page avec 8 visuels. Supprimez ceux qui répètent une information et reformulez les titres en phrases utiles.',
    autonomous: 'Pour le suivi d’un stock, choisissez 5 visuels maximum parmi carte KPI, barres, courbe, matrice, entonnoir et jauge. Justifiez chaque choix.',
    correction: 'Carte KPI pour stock critique, barres pour top produits à réapprovisionner, courbe pour évolution, matrice pour détail par entrepôt. L’entonnoir et la jauge ne sont conservés que si une étape ou une cible est réellement suivie.',
    project: 'Refonte visuelle : partez de votre premier rapport et livrez une page « Vue dirigeant » avec une hiérarchie claire, une palette de 3 couleurs et une annotation des choix.'
  },
  {
    id: 8, title: 'Interactions et rapport professionnel', short: 'Construire une expérience interactive.', time: '1 h 05', lessons: 4, status: 'locked', kicker: 'DESIGN DU RAPPORT', subtitle: 'Filtres, segments, drill-through : guidez l’exploration sans perdre le lecteur.',
    objectives: ['Configurer filtres, segments et interactions entre visuels.', 'Créer une page de détail avec drill-through.', 'Organiser la navigation et l’accessibilité.'], prereq: 'Avoir une page de rapport avec plusieurs visuels.',
    content: `<h2>Interagir sans se perdre</h2><p>Une interaction est utile quand elle permet de poser une nouvelle question. Les segments exposent un filtre important, le volet Filtres sert aux réglages plus fins, le drill-through emmène vers une page de détail et les info-bulles donnent du contexte au survol.</p><div class="definition-card"><div class="definition-icon">⌁</div><div><strong>Drill-through</strong><p>Un passage d’une vue synthétique vers une page détaillée en conservant le contexte sélectionné. C’est comme demander « montre-moi les pièces de ce dossier » depuis une vue de classement.</p></div></div><div class="capture-placeholder"><span>▧</span><div><strong>Capture à insérer — Modifier les interactions</strong><p>Montrer le ruban Format → Modifier les interactions avec les icônes Filtrer, Surligner et Aucun au-dessus des visuels.</p></div></div><h2>Une architecture de pages</h2><ol><li><strong>01 · Vue d’ensemble :</strong> les décisions et KPI essentiels.</li><li><strong>02 · Analyse :</strong> tendances, comparaisons et segments.</li><li><strong>03 · Détail :</strong> table ou drill-through pour vérifier.</li><li><strong>04 · Méthode :</strong> définitions, source et date d’actualisation.</li></ol>`,
    demo: { title: 'Ajouter un drill-through Produit', steps: ['Créer une nouvelle page et la nommer Détail Produit.', 'Dans la zone Drill-through, déposer D_Produit[NomProduit].', 'Ajouter une carte Total Ventes et un tableau de transactions.', 'Sur la page d’analyse, clic droit sur un produit → Drill-through → Détail Produit.', 'Ajouter un bouton Retour sur la page de détail.'], result: 'Le clic droit sur un produit ouvre une page contextualisée, et le bouton Retour ramène à la vue précédente.' },
    formula: { name: 'Mesure de contrôle', code: 'Lignes Visibles = COUNTROWS(FILTER(F_Ventes, [Total Ventes] > 0))', explanation: 'FILTER retourne les lignes qui respectent une condition ; COUNTROWS compte le résultat. Cette mesure peut alimenter une info-bulle ou un contrôle qualité.' },
    errors: ['Laisser les interactions par défaut sans vérifier qu’elles correspondent à l’intention.', 'Créer des segments sur 20 colonnes et rendre la page illisible.', 'Ne pas prévoir de bouton Retour ou de navigation explicite.'],
    best: ['Limiter les segments aux filtres réellement fréquents.', 'Afficher la période et les filtres actifs dans le sous-titre.', 'Prévoir une version clavier, un contraste suffisant et des textes alternatifs.'],
    guided: 'Ajoutez un segment Année, un segment Catégorie, une info-bulle avec Marge et un drill-through vers le détail d’un client.',
    autonomous: 'Construisez une navigation de 3 pages avec boutons et testez-la comme un utilisateur qui n’a jamais vu votre rapport.',
    correction: 'La page d’accueil doit mener vers Analyse et Détail. Chaque page doit avoir un bouton Retour ou Accueil. Les segments Année et Catégorie doivent filtrer les visuels prévus, pas les éléments décoratifs.',
    project: 'Prototype professionnel : documentez le parcours d’un utilisateur depuis le KPI en alerte jusqu’à la ligne de transaction qui explique l’écart.'
  },
  {
    id: 9, title: 'Publier avec Power BI Service', short: 'Partager un rapport qui reste vivant.', time: '1 h', lessons: 4, status: 'locked', kicker: 'POWER BI SERVICE', subtitle: 'Du fichier local à un espace de travail accessible et actualisable.',
    objectives: ['Publier un rapport depuis Desktop vers un espace de travail.', 'Distinguer rapport, tableau de bord, application et jeu de données.', 'Configurer une actualisation et partager avec méthode.'], prereq: 'Compte professionnel compatible et rapport enregistré.',
    content: `<h2>Desktop construit, Service diffuse</h2><p>Power BI Service est l’environnement web où l’on publie, partage et administre. Un fichier <strong>.pbix</strong> publié donne généralement un rapport et un modèle sémantique. Un tableau de bord peut épingler des éléments provenant de plusieurs rapports. Une application regroupe un contenu validé pour des lecteurs.</p><div class="definition-card"><div class="definition-icon">↗</div><div><strong>Espace de travail</strong><p>Un espace partagé où une équipe construit et gouverne son contenu. Ce n’est pas un simple dossier : il possède des rôles, des droits et un cycle de publication.</p></div></div><div class="capture-placeholder"><span>▧</span><div><strong>Capture à insérer — publication</strong><p>Montrer le bouton Publier dans Power BI Desktop, la sélection d’un espace de travail puis le message de publication réussie dans Service.</p></div></div><h2>Actualiser sans surprise</h2><p>Une actualisation relance les requêtes et met à jour le modèle. Pour une source locale, une passerelle (gateway) peut être nécessaire. Pour une source cloud, les informations d’identification et la fréquence doivent être configurées dans les paramètres du modèle.</p>`,
    demo: { title: 'Publier le rapport Contoso', steps: ['Dans Desktop, enregistrer et cliquer sur Publier.', 'Choisir l’espace de travail de test et attendre la confirmation.', 'Dans Service, ouvrir le rapport et contrôler les filtres.', 'Dans les paramètres du modèle, repérer les identifiants et l’historique d’actualisation.', 'Copier le lien uniquement pour les utilisateurs autorisés.'], result: 'Le rapport en ligne présente les mêmes résultats que Desktop et son propriétaire sait quand les données ont été actualisées.' },
    formula: { name: 'Règle de fraîcheur', code: 'Fraîcheur = NOW() - MAX(D_Date[Date])', explanation: 'Cette mesure n’est qu’un repère : elle estime l’écart entre maintenant et la dernière date de données. La date réelle de chargement doit aussi être documentée par le processus d’actualisation.' },
    errors: ['Partager un lien avec « Toute personne ayant le lien » sans validation de la confidentialité.', 'Publier dans l’espace personnel un rapport attendu par une équipe.', 'Ne pas tester les identifiants ou l’actualisation après publication.'],
    best: ['Nommer clairement espace, rapport, propriétaire et fréquence.', 'Ajouter une page « À propos » avec source, date et définitions.', 'Tester le rapport dans Service, pas seulement dans Desktop.'],
    guided: 'Publiez un rapport dans un espace de test, documentez l’URL, le propriétaire, la fréquence et le résultat d’une actualisation manuelle.',
    autonomous: 'Imaginez une équipe de 25 commerciaux. Définissez qui construit, qui valide, qui lit et qui reçoit l’alerte en cas d’échec d’actualisation.',
    correction: 'Exemple : contributeurs = analystes ; membre propriétaire = responsable BI ; lecteurs = commerciaux ; validation = direction commerciale ; alerte d’échec = propriétaire et administrateur.',
    project: 'Mise en ligne contrôlée : publiez votre rapport final dans un espace de test, créez une application ou un accès lecteur et livrez une fiche de mise à disposition.'
  },
  {
    id: 10, title: 'Sécurité et gouvernance', short: 'Partager la bonne donnée à la bonne personne.', time: '55 min', lessons: 3, status: 'locked', kicker: 'GOUVERNANCE', subtitle: 'La confiance dans un dashboard passe aussi par ses règles d’accès.',
    objectives: ['Comprendre les rôles de partage et la sécurité au niveau des lignes.', 'Identifier données sensibles, propriétaires et règles de conservation.', 'Mettre en place une checklist de gouvernance.'], prereq: 'Module 9 et connaissance de votre environnement Microsoft 365.',
    content: `<h2>La sécurité n’est pas une option finale</h2><p>Un rapport peut être techniquement juste et pourtant mal gouverné. La gouvernance définit qui peut voir, modifier, partager et supprimer. Elle inclut aussi le glossaire, le propriétaire, la qualité, la traçabilité et le cycle de vie.</p><div class="definition-card"><div class="definition-icon">◉</div><div><strong>RLS — Row-Level Security</strong><p>La sécurité au niveau des lignes limite les données visibles selon l’utilisateur connecté. Un commercial peut voir sa région sans qu’une copie différente du rapport soit nécessaire.</p></div></div><div class="capture-placeholder"><span>▧</span><div><strong>Capture à insérer — rôles de sécurité</strong><p>Montrer Modélisation → Gérer les rôles dans Desktop, avec un rôle Région et une expression de filtre sur la dimension commerciale.</p></div></div><h2>La checklist de confiance</h2><ul><li>La source et la fréquence sont-elles visibles ?</li><li>Chaque KPI a-t-il une définition validée ?</li><li>Les personnes ont-elles le minimum de droits nécessaire ?</li><li>Les données personnelles sont-elles masquées, minimisées ou protégées ?</li><li>Le propriétaire sait-il quoi faire en cas d’échec d’actualisation ?</li></ul>`,
    demo: { title: 'Créer un rôle par région', steps: ['Dans Desktop → Modélisation → Gérer les rôles → Créer.', 'Ajouter un filtre sur D_Region[NomRegion] selon une valeur de test.', 'Tester le rôle avec Afficher comme rôle.', 'Publier puis affecter des utilisateurs ou groupes dans Service.', 'Documenter la règle et sa date de revue.'], result: 'Un utilisateur de test ne voit que les lignes de sa région et les totaux correspondent à ce périmètre.' },
    formula: { name: 'Filtre de rôle simple', code: 'D_Region[NomRegion] = "Nord"', explanation: 'Cette expression limite les lignes de la dimension à la valeur Nord. Dans un vrai projet, préférez souvent une table d’habilitation liée à l’utilisateur connecté.' },
    errors: ['Tester la RLS avec un compte administrateur qui voit tout.', 'Protéger le rapport mais laisser le fichier source ouvert à tous.', 'Oublier de revoir les habilitations quand une personne change de poste.'],
    best: ['Utiliser des groupes plutôt que des droits individuels quand c’est possible.', 'Conserver une matrice des rôles et un propriétaire de revue.', 'Ne jamais mettre un secret ou une donnée personnelle dans une capture ou un fichier d’exercice.'],
    guided: 'Écrivez la matrice d’accès d’un rapport RH : direction, managers, RH et collaborateurs. Pour chaque rôle, listez ce qui est visible et modifiable.',
    autonomous: 'Proposez une stratégie RLS pour une société avec 4 régions et 2 responsables par région. Quel est le risque d’un filtre codé en dur ?',
    correction: 'Une table Habilitations contenant Email et Région permet de filtrer dynamiquement avec USERPRINCIPALNAME(). Un filtre codé en dur ne s’adapte pas aux utilisateurs et multiplie les rôles à maintenir.',
    project: 'Audit de confiance : remplissez la checklist gouvernance de votre rapport, ajoutez la page Méthode et produisez une matrice des droits.'
  },
  {
    id: 11, title: 'Projet guidé : cockpit commercial', short: 'Assembler une solution complète sur un cas réel.', time: '2 h 30', lessons: 3, status: 'locked', kicker: 'PROJET GUIDÉ', subtitle: 'Vous allez livrer un dashboard commercial de bout en bout, comme en entreprise.',
    objectives: ['Cadrer un besoin à partir de questions métier.', 'Livrer un modèle propre, des mesures testées et une page dirigeant.', 'Présenter vos choix et vérifier la qualité avant publication.'], prereq: 'Modules 1 à 10. Utiliser le jeu de données Contoso.',
    content: `<h2>Le brief</h2><p>La direction commerciale veut comprendre pourquoi le chiffre d’affaires du dernier trimestre varie selon les régions. Elle souhaite une vue synthétique, une analyse par produit et un détail exportable. Les données disponibles sont les ventes, les produits, les clients, les régions et un calendrier.</p><h3>Livrables attendus</h3><ul><li>Un modèle en étoile documenté.</li><li>Les mesures : Total Ventes, Marge, Marge %, Clients Uniques, Ventes N-1, Variation %.</li><li>Une page « Vue dirigeant » et une page « Analyse produit ».</li><li>Une page À propos avec source, date d’actualisation et définitions.</li><li>Une note de test avec au moins 5 contrôles de cohérence.</li></ul><div class="capture-placeholder"><span>▧</span><div><strong>Capture à insérer — livrable final</strong><p>Insérer une capture anonymisée de la vue dirigeant : 3 KPI, tendance, comparaison régionale, segment période et annotation d’un point important.</p></div></div><h2>La revue de qualité</h2><p>Comparez un échantillon de totaux avec la source. Cliquez sur chaque segment. Testez un mois sans données. Vérifiez l’affichage sur une fenêtre plus petite. Faites relire le rapport par une personne qui connaît le métier et une personne qui ne le connaît pas.</p>`,
    demo: { title: 'Plan de livraison en 6 passes', steps: ['Pass 1 — cadrage : écrire les questions et la définition de chaque KPI.', 'Pass 2 — données : nettoyer, typer, documenter les sources.', 'Pass 3 — modèle : relations, table de dates, champs masqués.', 'Pass 4 — calculs : mesures atomiques puis indicateurs dérivés.', 'Pass 5 — récit : synthèse, analyse, détail, navigation.', 'Pass 6 — contrôle : valeurs, filtres, accessibilité, partage.'], result: 'Un livrable professionnel se juge autant sur sa fiabilité et son usage que sur son apparence.' },
    formula: { name: 'Marge et marge %', code: 'Marge % = DIVIDE([Marge], [Total Ventes], 0)', explanation: 'La marge en valeur est une mesure de base. La marge % réutilise cette mesure et protège le cas où le chiffre d’affaires est nul.' },
    errors: ['Commencer par les couleurs avant de valider les chiffres.', 'Multiplier les KPI jusqu’à noyer la décision principale.', 'Livrer sans expliquer la source et les limites du modèle.'],
    best: ['Versionner les fichiers et noter les changements.', 'Faire valider les définitions par le métier.', 'Conserver une page de contrôle hors de la vue dirigeant.'],
    guided: 'Utilisez le brief pour écrire votre page de cadrage puis construisez le modèle et les quatre premières mesures avant de styliser.',
    autonomous: 'Présentez votre rapport en 5 minutes : problème, message principal, preuve dans les données, action recommandée, limites.',
    correction: 'Une bonne présentation ne récite pas les graphiques. Elle commence par une conclusion (« la région Sud décroche sur la catégorie X »), montre les visuels qui la démontrent puis propose une action et indique les limites.',
    project: 'Livraison intermédiaire : exportez une capture de la page dirigeant et une fiche de mesures. Demandez un retour à une personne et notez les corrections dans Mes notes.'
  },
  {
    id: 12, title: 'Projet final : votre dashboard de référence', short: 'Prouver votre autonomie sur un cas de votre choix.', time: '4 h', lessons: 5, status: 'locked', kicker: 'CAPSTONE', subtitle: 'Un dernier projet pour transformer les acquis en portfolio professionnel.',
    objectives: ['Concevoir un projet complet de la question métier au partage.', 'Justifier chaque choix de modèle, calcul et visualisation.', 'Présenter un rapport fiable, lisible et maintenable.'], prereq: 'Tous les modules précédents. Choisir ventes, stocks, RH, éducation, finance ou agriculture.',
    content: `<h2>Votre mission</h2><p>Choisissez un domaine que vous connaissez ou souhaitez explorer. Le projet doit répondre à un vrai besoin de pilotage et aboutir à un rapport interactif. Le sujet importe moins que la qualité de votre démarche : question, données, modèle, mesures, récit et gouvernance.</p><div class="definition-card"><div class="definition-icon">✦</div><div><strong>Le portfolio avant la perfection</strong><p>Un bon projet montre vos décisions et vos contrôles. Une capture esthétique ne suffit pas : documentez ce que vous avez exclu, les limites des données et les améliorations possibles.</p></div></div><h3>Grille d’évaluation</h3><table class="comparison-table"><thead><tr><th>CRITÈRE</th><th>ATTENDU</th><th>POIDS</th></tr></thead><tbody><tr><td>Besoin et récit</td><td>Questions et public clairement définis</td><td>20 %</td></tr><tr><td>Données et modèle</td><td>Power Query propre, modèle en étoile</td><td>25 %</td></tr><tr><td>DAX et fiabilité</td><td>Mesures justes, contrôles documentés</td><td>25 %</td></tr><tr><td>Design et usage</td><td>Hiérarchie, interactions, accessibilité</td><td>20 %</td></tr><tr><td>Gouvernance</td><td>Source, sécurité, actualisation, limites</td><td>10 %</td></tr></tbody></table><div class="capture-placeholder"><span>▧</span><div><strong>Capture à insérer — soutenance</strong><p>Prévoir une capture du dashboard final et une photo ou un schéma du modèle. Ne jamais afficher de données personnelles réelles.</p></div></div><h2>Votre checklist finale</h2><ol><li>Le besoin tient en une phrase et les utilisateurs sont identifiés.</li><li>Chaque relation et mesure a une raison d’être.</li><li>Les résultats principaux ont été comparés à une source.</li><li>Les filtres et interactions ne créent pas de surprise.</li><li>La date de rafraîchissement et les limites sont visibles.</li><li>Le rapport peut être repris par une autre personne.</li></ol>`,
    demo: { title: 'Préparer une soutenance de 7 minutes', steps: ['Minute 1 : contexte et décision à aider.', 'Minutes 2–3 : vue d’ensemble et message principal.', 'Minutes 4–5 : exploration d’un écart avec filtres et détail.', 'Minute 6 : modèle, mesures ou contrôle qualité qui rendent le résultat fiable.', 'Minute 7 : recommandation, limites et prochaine étape.'], result: 'Vous démontrez votre autonomie : vous savez expliquer le pourquoi, pas seulement montrer le comment.' },
    formula: { name: 'Indicateur de couverture', code: 'Couverture Données = DIVIDE([Lignes Contrôlées], [Lignes Totales], 0)', explanation: 'Un KPI de couverture vous aide à rendre visible la qualité d’un périmètre, plutôt que de laisser l’utilisateur supposer que les données sont complètes.' },
    errors: ['Changer de sujet au dernier moment et ne pas finir la partie qualité.', 'Cacher les limites des données pour donner une impression de certitude.', 'Copier un modèle sans savoir expliquer la granularité ou le contexte DAX.'],
    best: ['Faire une version minimale fonctionnelle, puis améliorer.', 'Utiliser une convention de nommage constante.', 'Demander un retour tôt, avant la finition graphique.'],
    guided: 'Écrivez votre fiche projet en une page : contexte, public, décisions, sources, tables, 5 KPI, 3 pages, sécurité et limites.',
    autonomous: 'Livrez le rapport complet et enregistrez une courte présentation audio ou vidéo de votre démarche.',
    correction: 'Comparez votre livrable à la grille d’évaluation, demandez une note argumentée à un pair et listez trois améliorations prioritaires. La correction est votre capacité à justifier et améliorer.',
    project: 'Projet final NEXORA : publiez votre dashboard, sa documentation et votre présentation. Ajoutez le lien ou les captures à votre portfolio en respectant la confidentialité.'
  }
];

const formulas = [
  {name:'SUM', tag:'Agrégation', code:'Total Ventes = SUM(F_Ventes[Montant])', description:'Additionne toutes les valeurs numériques d’une colonne dans le contexte courant.', result:'248 620 €', use:'Total, quantité, coûts ou toute valeur additive.', error:'SUM ne déduplique pas : pour compter des clients, utilisez DISTINCTCOUNT.'},
  {name:'AVERAGE', tag:'Agrégation', code:'Panier Moyen = AVERAGE(F_Ventes[Montant])', description:'Calcule la moyenne des valeurs non vides d’une colonne.', result:'86,40 €', use:'Notes, délais, panier ou durée moyenne.', error:'La moyenne des lignes n’est pas toujours la moyenne des groupes.'},
  {name:'DISTINCTCOUNT', tag:'Comptage', code:'Clients Uniques = DISTINCTCOUNT(F_Ventes[IDClient])', description:'Compte les valeurs distinctes d’une colonne.', result:'1 284', use:'Clients, étudiants, tickets ou employés uniques.', error:'Une colonne vide peut être comptée comme une valeur distincte.'},
  {name:'CALCULATE', tag:'Filtrage', code:'Ventes Premium = CALCULATE([Total Ventes], D_Produit[Segment] = "Premium")', description:'Évalue une expression dans un contexte de filtre modifié.', result:'92 180 €', use:'Comparaisons, segments, objectifs et scénarios.', error:'Le filtre ajouté modifie le contexte : testez toujours dans un tableau.'},
  {name:'FILTER', tag:'Filtrage', code:'Ventes Positives = CALCULATE([Total Ventes], FILTER(F_Ventes, F_Ventes[Montant] > 0))', description:'Retourne une table filtrée par une condition détaillée.', result:'247 910 €', use:'Conditions complexes qui ne tiennent pas dans un filtre simple.', error:'FILTER sur une table entière peut être coûteux : filtrez la dimension si possible.'},
  {name:'ALL', tag:'Filtrage', code:'Part du Total = DIVIDE([Total Ventes], CALCULATE([Total Ventes], ALL(D_Produit)))', description:'Ignore les filtres de la table ou colonne indiquée.', result:'100 %', use:'Parts du total, rangs et comparaisons avec une base fixe.', error:'ALL peut ignorer un filtre attendu : vérifiez le résultat avec les segments.'},
  {name:'IF / SWITCH', tag:'Logique', code:'Statut = SWITCH(TRUE(), [Variation %] > .1, "Fort", [Variation %] >= -.1, "Stable", "À surveiller")', description:'IF teste une condition ; SWITCH organise plusieurs cas de façon lisible.', result:'Fort', use:'Statuts, alertes, catégories et règles métier.', error:'Des IF imbriqués deviennent vite illisibles : préférez SWITCH(TRUE()).'},
  {name:'DATEADD', tag:'Temps', code:'Ventes N-1 = CALCULATE([Total Ventes], DATEADD(D_Date[Date], -1, YEAR))', description:'Décale le contexte de dates pour comparer une période.', result:'209 980 €', use:'N-1, mois précédent, tendance et variations.', error:'La table de dates doit être continue et correctement reliée.'},
  {name:'COUNT / COUNTA', tag:'Comptage', code:'Commandes = COUNT(F_Ventes[IDCommande])', description:'COUNT compte les valeurs numériques ; COUNTA compte les valeurs non vides, quel que soit leur type.', result:'2 876', use:'Compter des identifiants numériques ou des lignes renseignées.', error:'COUNT ne compte pas une colonne texte : utilisez COUNTA ou COUNTROWS selon la question.'},
  {name:'MIN / MAX', tag:'Agrégation', code:'Dernière Vente = MAX(F_Ventes[DateVente])', description:'Retourne la plus petite ou la plus grande valeur d’une colonne.', result:'30/09/2026', use:'Bornes de période, note maximale, prix minimum ou dernière activité.', error:'Une valeur extrême peut être une anomalie : contrôlez le type et les données.'},
  {name:'IF', tag:'Logique', code:'Alerte = IF([Stock Disponible] < [Seuil], "Réapprovisionner", "OK")', description:'Retourne une valeur si une condition est vraie et une autre dans le cas contraire.', result:'Réapprovisionner', use:'Règle binaire, seuil et indicateur d’alerte.', error:'Ne multipliez pas les IF imbriqués quand SWITCH rendrait la règle lisible.'},
  {name:'AND / OR / NOT', tag:'Logique', code:'Risque = IF(AND([Marge %] < .1, [Variation %] < 0), "Oui", "Non")', description:'AND exige que toutes les conditions soient vraies ; OR une seule ; NOT inverse une condition.', result:'Oui', use:'Combiner des règles métier et détecter des cas à surveiller.', error:'Parenthéser chaque condition et tester les cas limites, notamment les valeurs vides.'},
  {name:'TOTALYTD', tag:'Temps', code:'Ventes Cumulées = TOTALYTD([Total Ventes], D_Date[Date])', description:'Calcule le total cumulé depuis le début de l’année dans le contexte courant.', result:'248 620 €', use:'Suivi d’objectif annuel et courbe cumulative.', error:'Sans table de dates continue, le cumul peut être incomplet.'},
  {name:'MEDIAN / PERCENTILE', tag:'Statistique', code:'Médiane Délai = MEDIAN(F_Commandes[DelaiJours])', description:'MEDIAN donne la valeur centrale ; PERCENTILEX.INC permet de suivre un seuil de distribution.', result:'6 jours', use:'Délais, notes, montants ou toute distribution avec valeurs extrêmes.', error:'Une médiane ne remplace pas l’effectif : affichez les deux.'},
  {name:'STDEV.P', tag:'Statistique', code:'Dispersion = STDEV.P(F_Commandes[DelaiJours])', description:'Mesure la dispersion d’une population autour de sa moyenne.', result:'2,7 jours', use:'Stabilité d’un délai ou variabilité d’un résultat.', error:'Ne comparez pas des écarts-types de populations ou unités différentes sans contexte.'}
];

const glossary = [
  {t:'Actualisation', d:'Relancer les requêtes pour recharger le modèle avec les données les plus récentes. Elle peut être manuelle ou planifiée dans Power BI Service.'},
  {t:'Agrégation', d:'Résumer plusieurs valeurs en un seul résultat. Exemples : SUM pour additionner, AVERAGE pour la moyenne, DISTINCTCOUNT pour les valeurs uniques.'},
  {t:'Ajouter des requêtes', d:'Empiler des lignes de tables qui ont les mêmes colonnes : janvier + février + mars. À ne pas confondre avec Fusionner.'},
  {t:'Application Power BI', d:'Regroupement web de rapports et pages validés, destiné à un public de lecteurs avec un accès simple.'},
  {t:'Axe', d:'Zone d’un visuel qui accueille les catégories ou les dates. Exemple : les mois le long d’une courbe.'},
  {t:'Business Intelligence (BI)', d:'Méthodes et outils qui transforment les données en informations utiles à la décision. Le tableau de bord n’est pas le décideur : il éclaire celui qui décide.'},
  {t:'Cadrage', d:'Définir le besoin, le public, les décisions, les sources et la fréquence avant de construire. Une demande comme « un dashboard » devient une question précise.'},
  {t:'CALCULATE', d:'Fonction centrale de DAX : évalue une mesure dans un contexte de filtre modifié. Exemple : le total des ventes mais seulement pour le segment Premium.'},
  {t:'Carte KPI', d:'Visuel qui affiche une valeur clé, souvent avec une variation. Sert à attirer l’œil sur le niveau actuel d’un indicateur.'},
  {t:'Colonne calculée', d:'Colonne ajoutée au modèle, calculée ligne par ligne à l’actualisation. Utile pour créer un libellé ou un segment stable.'},
  {t:'Contexte de filtre', d:'Ensemble des filtres actifs autour d’une mesure (segments, page, visuel). La même mesure donne un résultat différent selon ce contexte.'},
  {t:'Contexte de ligne', d:'Point de vue d’une formule de colonne sur une ligne donnée. Une colonne calculée s’évalue ligne par ligne ; une mesure s’évalue selon les filtres.'},
  {t:'DAX', d:'Langage des formules de Power BI. Il ressemble à Excel mais travaille sur des tableaux entiers et réagit aux filtres du rapport.'},
  {t:'Dimension', d:'Table de description qui répond à qui, quoi, quand, où : produit, client, date, région. Elle filtre la table de faits.'},
  {t:'DirectQuery', d:'Mode de connexion qui interroge la source à la volée, sans copier les données. Utile pour la fraîcheur, au prix d’une dépendance à la source.'},
  {t:'DIVIDE', d:'Division protégée contre le dénominateur nul. Préférée à « / » pour un taux : DIVIDE(a, b, 0) renvoie 0 si b vaut zéro.'},
  {t:'Drill-through', d:'Passage d’une vue synthétique vers une page de détail en gardant le contexte sélectionné. Exemple : clic droit sur un produit → transactions détaillées.'},
  {t:'Drill-down', d:'Descendre dans une hiérarchie d’un visuel : année → trimestre → mois, puis remonter.'},
  {t:'Espace de travail', d:'Espace web partagé où une équipe publie et gouverne son contenu, avec des rôles (membre, contributeur, lecteur…).'},
  {t:'Écart-type', d:'Mesure de dispersion autour de la moyenne. Un écart-type élevé signale des valeurs très hétérogènes.'},
  {t:'Étapes appliquées', d:'Historique des transformations dans Power Query. Chaque étape est rejouée à la prochaine actualisation : c’est la recette de nettoyage.'},
  {t:'Filtre de page', d:'Filtre qui s’applique à tous les visuels d’une page. Exemple : afficher uniquement le trimestre en cours.'},
  {t:'Filtre de rapport', d:'Filtre qui s’applique à toutes les pages du rapport. Utile pour restreindre tout le rapport à une période ou une entité.'},
  {t:'Fusionner des requêtes', d:'Rapprocher des colonnes de deux tables grâce à une clé commune, comme une jointure. Exemple : ajouter le nom du produit aux ventes.'},
  {t:'Gateway (passerelle)', d:'Pont sécurisé entre Power BI Service et une source de données située sur le réseau local de l’organisation.'},
  {t:'Granularité', d:'Ce qu’une ligne d’une table représente. Dans F_Ventes : une ligne de vente pour un produit, un client et une date. À écrire avant toute mesure.'},
  {t:'Import (mode)', d:'Mode de connexion qui charge une copie des données dans le modèle. C’est le mode le plus courant et le plus rapide à l’affichage.'},
  {t:'Info-bulle', d:'Détail affiché au survol d’un élément. Elle complète un visuel sans l’encombrer.'},
  {t:'KPI', d:'Indicateur clé relié à une décision. Sans décision associée, un chiffre reste un simple affichage.'},
  {t:'Langage M', d:'Langage des requêtes Power Query. L’interface génère le code : le lire suffit pour diagnostiquer une étape.'},
  {t:'Médiane', d:'Valeur qui sépare la distribution en deux moitiés. Contrairement à la moyenne, elle résiste aux valeurs extrêmes.'},
  {t:'Mesure', d:'Calcul dynamique évalué selon les filtres du visuel. Idéale pour les KPI : elle ne stocke pas de résultat dans le modèle.'},
  {t:'Modèle en étoile', d:'Organisation avec une table de faits au centre et des dimensions autour. Simple à lire et aux filtres prévisibles.'},
  {t:'Modèle sémantique', d:'Couche de données publiée dans Service qui alimente les rapports, les scores et les connections partagées.'},
  {t:'N-1', d:'Période précédente : mois précédent, trimestre précédent ou année précédente. La référence d’une comparaison temporelle.'},
  {t:'Percentile', d:'Seuil en dessous duquel se trouve une proportion d’observations. Le P90 d’un délai indique le délai dépassé par 10 % des cas.'},
  {t:'Power BI Desktop', d:'Application locale où l’on connecte, modèle, calcule et dessine le rapport. Le fichier de travail s’appelle .pbix.'},
  {t:'Power BI Service', d:'Plateforme web où l’on publie, partage, actualise et administre les rapports.'},
  {t:'Power Query', d:'Moteur de connexion et de transformation : il nettoie et structure les données avant le modèle.'},
  {t:'Requête', d:'Recette qui décrit le passage de la source à une table prête à l’emploi : quelles étapes, dans quel ordre.'},
  {t:'RLS (Row-Level Security)', d:'Sécurité au niveau des lignes : chaque utilisateur ne voit que les lignes qui le concernent. Exemple : un responsable ne voit que sa région.'},
  {t:'Segment', d:'Filtre visible et manipulable par le lecteur, posé sur un visuel ou une page.'},
  {t:'Signet (bookmark)', d:'État d’un rapport enregistré (filtres, visibilité) auquel on peut revenir en un clic.'},
  {t:'SWITCH(TRUE())', d:'Motif DAX lisible pour plusieurs conditions : les cas sont évalués dans l’ordre, comme une pile de règles.'},
  {t:'Table calculée', d:'Table créée par une formule DAX, calculée à l’actualisation. À réserver aux besoins ciblés de modélisation.'},
  {t:'Table de dates', d:'Table continue d’un jour à l’autre, reliée au fait et marquée comme table de dates. Indispensable pour N-1 et les cumuls.'},
  {t:'Table de faits', d:'Table des événements mesurables : une ligne par vente, note ou commande. Elle contient les mesures et les clés étrangères.'},
  {t:'Visuel', d:'Élément graphique du rapport : courbe, barres, carte, matrice. Chaque visuel répond à une question précise.'}
];


const quizzes = {
  1: [
    {q:'Quelle est la différence entre une donnée et une information ?', o:['L’information est organisée pour répondre à une question','La donnée est toujours chiffrée','L’information est plus ancienne'], a:0, why:'Une donnée est une trace brute ; l’information est mise en contexte pour éclairer une décision.'},
    {q:'À quoi sert principalement Power BI Service ?', o:['À installer les connecteurs localement','À publier, partager et actualiser les rapports','À écrire des requêtes SQL'], a:1, why:'Desktop construit, Service diffuse : publication, partage, actualisation et sécurité.'},
    {q:'Par quoi commence un projet BI réussi ?', o:['Par le choix des couleurs','Par une décision à améliorer','Par l’import de toutes les sources'], a:1, why:'Sans décision associée, un indicateur reste un chiffre décoratif.'}
  ],
  2: [
    {q:'Quel fichier contient le modèle et le rapport Power BI Desktop ?', o:['Le classeur .xlsx','Le fichier .pbix','Le fichier .csv'], a:1, why:'Le .pbix rassemble requêtes, modèle, mesures et pages de rapport.'},
    {q:'Par où commence l’import d’un fichier Excel ?', o:['Accueil → Obtenir les données → Excel','Fichier → Imprimer','Modélisation → Nouvelle table'], a:0, why:'Toute connexion part d’Accueil → Obtenir les données, puis on choisit Transformer ou Charger.'},
    {q:'Une colonne texte déposée dans « Valeurs » produit par défaut…', o:['une somme','un comptage','une moyenne'], a:1, why:'Power BI compte les valeurs texte ; vérifiez toujours l’agrégation proposée et changez-la si besoin.'}
  ],
  3: [
    {q:'Où Power BI enregistre-t-il chaque transformation ?', o:['Dans le volet Étapes appliquées','Dans la vue Modèle','Dans le fichier source'], a:0, why:'Chaque clic devient une étape rejouable à la prochaine actualisation.'},
    {q:'Empiler les ventes de janvier et février revient à…', o:['Fusionner des requêtes','Ajouter des requêtes','Croiser des tables'], a:1, why:'Ajouter empile des lignes de même structure ; Fusionner rapproche des colonnes par une clé.'},
    {q:'Pourquoi ne pas corriger directement le fichier Excel ?', o:['Excel est trop lourd','La correction ne serait pas rejouée à l’actualisation','Power BI interdit d’ouvrir Excel'], a:1, why:'La règle doit vivre dans Power Query pour être rejouée sur chaque nouvelle extraction.'}
  ],
  4: [
    {q:'Quelle relation produit un modèle en étoile correct entre un produit et une vente ?', o:['*:* entre les deux tables','1:* avec le 1 sur D_Produit','1:1 partout'], a:1, why:'Un produit apparaît dans plusieurs ventes : le côté 1 est sur la dimension, le * sur le fait.'},
    {q:'Quelle table contient les événements mesurables ?', o:['La table de faits','La table de dimension','La table de dates'], a:0, why:'Le fait répond à « combien » : une ligne de vente, une note, une commande.'},
    {q:'Pourquoi une table de dates continue est-elle indispensable ?', o:['Pour trier les noms de mois','Pour les comparaisons N-1 et les cumuls','Pour réduire la taille du fichier'], a:1, why:'DATEADD et TOTALYTD ont besoin de chaque jour présent, relié au fait.'}
  ],
  5: [
    {q:'Quelle fonction calcule le chiffre d’affaires total ?', o:['COUNT','SUM','AVERAGE'], a:1, why:'SUM additionne une colonne numérique ; COUNT compte des valeurs.'},
    {q:'Comment compter chaque client une seule fois ?', o:['DISTINCTCOUNT','COUNTROWS','SUM'], a:0, why:'DISTINCTCOUNT élimine les doublons ; COUNTROWS compte toutes les lignes du fait.'},
    {q:'Quand une mesure est-elle calculée ?', o:['À l’affichage, selon les filtres','Une seule fois à l’import','Jamais, elle est stockée en dur'], a:0, why:'La mesure s’adapte au contexte de chaque visuel — c’est ce qui la différencie d’une colonne.'}
  ],
  6: [
    {q:'Que fait CALCULATE ?', o:['Modifie le contexte de filtre d’une mesure','Crée une nouvelle colonne','Trie un visuel'], a:0, why:'CALCULATE évalue une expression avec des filtres ajoutés ou retirés : la porte d’entrée du DAX analytique.'},
    {q:'Quelle fonction permet de calculer la part du total ?', o:['FILTER','ALL','MIN'], a:1, why:'ALL retire le filtre de la catégorie pour retrouver le dénominateur global.'},
    {q:'Comment obtenir les ventes de l’année précédente ?', o:['DATEADD(D_Date[Date], -1, YEAR)','SUM(-1)','NOW()'], a:0, why:'DATEADD décale le contexte de dates d’une année — à tester avec une table de dates continue.'}
  ],
  7: [
    {q:'Quel visuel raconte le mieux une évolution mensuelle ?', o:['La courbe avec axe temporel','Le camembert','Le graphique radar'], a:0, why:'Le temps se lit en continu ; un camembert par mois rend la comparaison impossible.'},
    {q:'Que fait mieux la médiane que la moyenne ?', o:['Elle résiste aux valeurs extrêmes','Elle additionne toujours','Elle évite les filtres'], a:0, why:'Une commande à 90 jours fausse la moyenne des délais mais peu la médiane.'},
    {q:'Pourquoi limiter les couleurs ?', o:['Gagner de la mémoire','Ne pas surcharger la mémoire visuelle du lecteur','Respecter une règle légale'], a:1, why:'Chaque couleur doit porter une information ; sinon le lecteur mémorise une inutile.'}
  ],
  8: [
    {q:'Quel mécanisme emmène vers une page de détail avec le contexte ?', o:['Le drill-through','Le signet','L’info-bulle'], a:0, why:'Le drill-through conserve la sélection courante pour ouvrir la page détaillée correspondante.'},
    {q:'Quel objet permet au lecteur de filtrer lui-même la page ?', o:['Le segment','Le titre','La légende'], a:0, why:'Le segment est un filtre visible et manipulable ; gardez-en seulement les plus utiles.'},
    {q:'Où vérifie-t-on l’effet d’un clic sur un autre visuel ?', o:['Accueil → Actualiser','Format → Modifier les interactions','Modélisation → Gérer les rôles'], a:1, why:'Chaque visuel source peut filtrer, surligner ou ignorer les autres : à contrôler explicitement.'}
  ],
  9: [
    {q:'Que produit un fichier .pbix publié dans Service ?', o:['Uniquement un PDF','Un rapport et un modèle sémantique','Une base SQL'], a:1, why:'Le rapport s’appuie sur un modèle sémantique qui gère données, mesures et actualisation.'},
    {q:'Quel élément relie Service à une source de données sur le réseau local ?', o:['La passerelle (gateway)','Le segment','Le signet'], a:0, why:'Sans passerelle, Service ne peut pas atteindre un fichier ou une base hébergés en interne.'},
    {q:'Avant de partager un rapport, que faut-il tester ?', o:['Seulement l’affichage dans Desktop','Ouvrir le rapport dans Service et comparer les résultats','Le thème sombre'], a:1, why:'Source, droits et actualisation ne se voient qu’une fois le contenu publié.'}
  ],
  10: [
    {q:'Que fait la RLS (Row-Level Security) ?', o:['Limite les lignes visibles selon l’utilisateur','Chiffre le fichier','Verrouille les visuels'], a:0, why:'Un responsable régional ne voit que sa région, sans copie de rapport.'},
    {q:'Avec quel compte tester un rôle RLS ?', o:['Le compte administrateur','Un compte lecteur de test','Aucun, le test est automatique'], a:1, why:'L’administrateur voit souvent tout : le test avec un vrai lecteur est le seul crédible.'},
    {q:'Que faire quand un collaborant quitte l’équipe ?', o:['Attendre la prochaine revue annuelle','Revoir ses habilitations et celles des groupes','Changer le mot de passe du rapport'], a:1, why:'Les droits minimaux et les revues régulières sont le cœur de la gouvernance.'}
  ],
  11: [
    {q:'Par où passe la première étape du projet cockpit commercial ?', o:['La définition écrite de chaque KPI','Le choix du thème visuel','La publication'], a:0, why:'Sans définition validée, la revue finale n’a aucun point de référence.'},
    {q:'Comment contrôler la fiabilité des totaux ?', o:['Faire confiance à Power BI','Rapprocher un échantillon de la source','Changer le type de visuel'], a:1, why:'Un contrôle écrit (source, valeur attendue, valeur obtenue) est la preuve de la fiabilité.'},
    {q:'Par quoi commence une bonne présentation de rapport ?', o:['La liste des graphiques','Une conclusion appuyée sur les données','L’historique de Power BI'], a:1, why:'Décision d’abord, preuves ensuite, limites enfin.'}
  ],
  12: [
    {q:'Quel critère pèse le plus dans la grille d’évaluation ?', o:['Le nombre de visuels','Les données, le modèle et le DAX','La couleur préférée'], a:1, why:'Modèle et calculs pèsent 25 % chacun : la fiabilité prime sur l’habillage.'},
    {q:'Que faire des limites des données dans un portfolio ?', o:['Les cacher pour rassurer','Les afficher comme preuve de maturité','Les supprimer du projet'], a:1, why:'Un analyste crédible documente ce que la donnée ne permet pas de conclure.'},
    {q:'Avant de publier des captures du projet final…', o:['Anonymiser les données réelles','Augmenter la résolution','Supprimer la page À propos'], a:0, why:'Aucune donnée personnelle ou confidentielle ne doit apparaître dans une capture publique.'}
  ]
};

let completedModules = JSON.parse(localStorage.getItem('nexora-completed') || '[1]');
let currentModule = Number(localStorage.getItem('nexora-current') || 2);
let currentRoute = 'dashboard';
let learnerName=(localStorage.getItem('nexora-name')||'Alex Martin').trim()||'Alex Martin';
let selectedFormula = 0;

const $ = (selector, parent=document) => parent.querySelector(selector);
const $$ = (selector, parent=document) => [...parent.querySelectorAll(selector)];

function getModule(id){ return modules.find(m => m.id === Number(id)) || modules[0]; }
function isUnlocked(m){ return m.id <= Math.max(...completedModules, 1) + 1; }
function progress(){ return Math.min(100, Math.round(((completedModules.length + (currentModule && !completedModules.includes(currentModule) ? .38 : 0)) / modules.length) * 100)); }
function showToast(message){ const toast=$('#toast'); toast.textContent=message; toast.classList.add('show'); clearTimeout(window.toastTimer); window.toastTimer=setTimeout(()=>toast.classList.remove('show'),3000); }

function quizScore(id){
  const qs=quizzes[id]||[], sv=savedQuiz(id);
  let score=0, answered=0;
  qs.forEach((q,i)=>{ if(sv[i]!=null){ answered++; if(sv[i]===q.a) score++; } });
  return {score, answered, total:qs.length};
}
function renderQuiz(m){
  const qs=quizzes[m.id]; if(!qs||!qs.length) return '';
  const sv=savedQuiz(m.id);
  const questions=qs.map((q,i)=>{
    const chosen=sv[i], answered=chosen!=null, correct=answered&&chosen===q.a;
    const options=q.o.map((o,ci)=>{
      let cls='quiz-option';
      if(answered){ if(ci===q.a) cls+=' correct'; else if(ci===chosen) cls+=' wrong'; }
      return `<button class="${cls}" data-quiz-mod="${m.id}" data-quiz-q="${i}" data-quiz-choice="${ci}" ${answered?'disabled':''}>${o}</button>`;
    }).join('');
    const fb=answered?`<p class="quiz-feedback ${correct?'ok':'ko'}">${correct?'✓ Exact. ':`✗ La bonne réponse était « ${q.o[q.a]} ». `}${q.why}</p>`:'';
    return `<div class="quiz-question"><p class="quiz-q"><b>Q${i+1}</b> ${q.q}</p><div class="quiz-options">${options}</div>${fb}</div>`;
  }).join('');
  const st=quizScore(m.id);
  const scoreLine=st.answered===st.total
    ?`<div class="quiz-score done">Score final : <strong>${st.score}/${st.total}</strong> ${st.score===st.total?'— parfait !':st.score>=2?'— module validé, relisez la question manquée.':'— relisez les parties indiquées avant d’aller plus loin.'}</div>`
    :`<div class="quiz-score">Répondues : <strong>${st.answered}/${st.total}</strong></div>`;
  const retry=st.answered===st.total?'<button class="text-button quiz-retry" id="reset-quiz">Recommencer le quiz <span>↺</span></button>':'';
  return `<h2>Vérifiez votre compréhension</h2><div class="quiz-block">${questions}${scoreLine}${retry}</div>`;
}
function handleQuizChoice(btn){
  const mod=Number(btn.dataset.quizMod), qi=Number(btn.dataset.quizQ), ch=Number(btn.dataset.quizChoice);
  const qs=quizzes[mod]; if(!qs) return;
  const sv=savedQuiz(mod); if(sv[qi]!=null) return;
  while(sv.length<qs.length) sv.push(null);
  sv[qi]=ch; saveQuiz(mod,sv); logActivity(1);
  const block=btn.closest('.quiz-question'), q=qs[qi], correct=ch===q.a;
  block.querySelectorAll('.quiz-option').forEach((b,ci)=>{ b.disabled=true; if(ci===q.a) b.classList.add('correct'); else if(ci===ch) b.classList.add('wrong'); });
  const fb=document.createElement('p'); fb.className='quiz-feedback '+(correct?'ok':'ko');
  fb.textContent=(correct?'✓ Exact. ':'✗ La bonne réponse était « '+q.o[q.a]+' ». ')+q.why;
  block.appendChild(fb);
  const st=quizScore(mod), scoreEl=document.querySelector('#lesson-article .quiz-score');
  if(scoreEl){
    if(st.answered===st.total){ scoreEl.className='quiz-score done'; scoreEl.innerHTML=`Score final : <strong>${st.score}/${st.total}</strong> ${st.score===st.total?'— parfait !':st.score>=2?'— module validé, relisez la question manquée.':'— relisez les parties indiquées.'}`; showToast(`Quiz terminé : ${st.score}/${st.total}.`); }
    else scoreEl.innerHTML=`Répondues : <strong>${st.answered}/${st.total}</strong>`;
  }
}
function localDayKey(d=new Date()){ return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`; }
function getActivity(){ try{ const a=JSON.parse(localStorage.getItem('nexora-activity')||'{}'); return a&&typeof a==='object'?a:{}; }catch(e){ return {}; } }
function logActivity(step=1){
  const a=getActivity(), key=localDayKey();
  a[key]=(a[key]||0)+step;
  localStorage.setItem('nexora-activity',JSON.stringify(a));
  renderActivity();
}
function renderActivity(){
  const bars=$('#activity-bars'), total=$('#activity-total'); if(!bars||!total) return;
  const act=getActivity();
  const days=[];
  for(let i=6;i>=0;i--){ const d=new Date(); d.setDate(d.getDate()-i); days.push(d); }
  const labels=['dim.','lun.','mar.','mer.','jeu.','ven.','sam.'];
  let sum=0;
  bars.innerHTML=days.map((d,i)=>{
    const n=act[localDayKey(d)]||0; sum+=n;
    const h=n?Math.min(100,25+n*25):6;
    return `<div class="${i===6?'today':''}${n?'':' empty'}"><span style="height:${h}%"></span><small>${labels[d.getDay()]}</small></div>`;
  }).join('');
  total.innerHTML=`<strong>${sum}</strong><span>action${sum>1?'s':''} cette semaine</span>`;
}
function applyName(){
  const first=learnerName.split(/\s+/)[0]||'Alex';
  const g=$('#greeting-name'); if(g) g.textContent=first;
  const pn=$('#profile-name'); if(pn) pn.textContent=learnerName;
  const ini=(learnerName.split(/\s+/).slice(0,2).map(w=>w[0]||'').join('')||'AM').toUpperCase();
  const a=$('#profile-initials'); if(a) a.textContent=ini;
  const m=$('#mini-avatar'); if(m) m.textContent=ini;
}
function renameProfile(){
  const next=(window.prompt('Votre prénom et nom :',learnerName)||'').trim();
  if(!next) return;
  learnerName=next; localStorage.setItem('nexora-name',next); applyName();
  showToast(`Bonjour ${next.split(/\s+/)[0]} ! Profil mis à jour.`);
}
function showModal(){ const o=$('#modal-overlay'); if(o){ o.hidden=false; document.body.classList.add('modal-open'); } }
function openCertificate(){
  const quizDone=modules.filter(m=>{const st=quizScore(m.id);return st.total&&st.answered===st.total;}).length;
  const date=new Intl.DateTimeFormat('fr-FR',{dateStyle:'long'}).format(new Date());
  $('#modal-content').innerHTML=`<p class="eyebrow">CERTIFICAT NEXORA</p><h2 id="modal-title">Power BI — Foundations</h2><div class="certificate-doc"><div class="cert-mark">✦ NEXORA · DATA ACADEMY</div><p>Ce certificat atteste que</p><h3>${escapeHtml(learnerName)}</h3><p class="cert-claim">a validé les 12 modules de la formation<br><strong>Power BI — de zéro à dashboard professionnel</strong></p><div class="cert-foot"><span>Délivré le ${date}</span><span>48 leçons · ${quizDone} quiz validés</span></div></div><div class="resource-actions"><button class="button button-dark" id="print-certificate">Imprimer le certificat</button></div>`;
  showModal();
  const pb=$('#print-certificate'); if(pb) pb.addEventListener('click',()=>window.print());
}
function savedQuiz(id){ let all={}; try{ all=JSON.parse(localStorage.getItem('nexora-quizzes')||'{}')||{}; }catch(e){} const arr=Array.isArray(all[id])?all[id]:[]; return arr; }
function saveQuiz(id,arr){ let all={}; try{ all=JSON.parse(localStorage.getItem('nexora-quizzes')||'{}')||{}; }catch(e){} all[id]=arr; localStorage.setItem('nexora-quizzes',JSON.stringify(all)); }
function exportProgress(){
  const data={version:1,exportedAt:new Date().toISOString(),completed:completedModules,current:currentModule,
    notes:JSON.parse(localStorage.getItem('nexora-notes')||'[]'),quizzes:JSON.parse(localStorage.getItem('nexora-quizzes')||'{}')};
  const blob=new Blob([JSON.stringify(data,null,2)],{type:'application/json'});
  const link=document.createElement('a'); link.href=URL.createObjectURL(blob); link.download='nexora_progression.json'; link.click(); URL.revokeObjectURL(link.href);
  showToast('Progression exportée (modules, quiz et notes).');
}
function importProgress(file){
  const reader=new FileReader();
  reader.onload=()=>{
    try{
      const d=JSON.parse(reader.result);
      if(!d||!Array.isArray(d.completed)) throw new Error('format');
      completedModules=d.completed.map(Number).filter(n=>Number.isInteger(n)&&n>=1&&n<=modules.length);
      if(!completedModules.length) completedModules=[1];
      localStorage.setItem('nexora-completed',JSON.stringify(completedModules));
      currentModule=Number(d.current)&&Number(d.current)>=1&&Number(d.current)<=modules.length?Number(d.current):2;
      localStorage.setItem('nexora-current',currentModule);
      if(Array.isArray(d.notes)) localStorage.setItem('nexora-notes',JSON.stringify(d.notes));
      if(d.quizzes&&typeof d.quizzes==='object') localStorage.setItem('nexora-quizzes',JSON.stringify(d.quizzes));
      updateProgressUI(); renderNotes(); showToast('Progression importée avec succès.');
    }catch(e){ showToast('Fichier invalide : import annulé.'); }
  };
  reader.readAsText(file);
}
function renderModuleCard(m){
  const done=completedModules.includes(m.id), current=m.id===currentModule && !done, unlocked=isUnlocked(m);
  return `<article class="module-card ${done?'done ':''}${current?'current ':''}${!unlocked?'locked':''}" data-module="${m.id}" ${!unlocked?'aria-disabled="true"':''}>
    <div class="module-card-top"><span>${String(m.id).padStart(2,'0')} · ${m.kicker}</span><span class="module-card-number">${done?'✓':String(m.id).padStart(2,'0')}</span></div>
    <h3>${m.title}</h3><p>${m.short}</p><div class="module-card-footer"><b>◷ ${m.time}</b><span class="card-state">${done?'Terminé':current?'En cours':!unlocked?'⌁ Verrouillé':'À venir'}</span>${(()=>{const st=quizzes[m.id]?quizScore(m.id):null;return st&&st.total&&st.answered===st.total?` <span class="card-quiz">Quiz ${st.score}/${st.total}</span>`:'';})()}</div>
  </article>`;
}
function renderDashboardModules(list=modules){ $('#dashboard-module-grid').innerHTML=list.map(renderModuleCard).join(''); }
function renderPath(list=modules){
  $('#path-list').innerHTML=list.map(m=>{const done=completedModules.includes(m.id), current=m.id===currentModule&&!done, unlocked=isUnlocked(m); return `<div class="path-row ${done?'done ':''}${current?'current ':''}" data-module="${m.id}"><div class="path-index">${done?'✓':String(m.id).padStart(2,'0')}</div><div class="path-body" ${!unlocked?'aria-disabled="true"':''}><div class="path-body-main"><div class="path-body-kicker">MODULE ${String(m.id).padStart(2,'0')} · ${m.kicker}</div><h3>${m.title}</h3><p>${m.short}</p></div><div class="path-body-meta">◷ ${m.time}</div><div class="path-state">${done?'Terminé':current?'En cours':!unlocked?'Verrouillé':'À venir'}</div></div></div>`}).join('');
}
function updateProgressUI(){
  const value=progress();
  $('#sidebar-progress-value').textContent=value+'%'; $('#sidebar-progress-bar').style.width=value+'%'; $('#completion-badge-value').textContent=value+'%';
  const small=$('.sidebar-progress small'); if(small) small.textContent=`${completedModules.length} module${completedModules.length>1?'s':''} sur 12 terminé${completedModules.length>1?'s':''}`;
  renderDashboardModules(); renderPath();
  const cert=$('#certificate-banner'); if(cert) cert.hidden=completedModules.length<modules.length;
}

function navigateView(route){
  currentRoute=route;
  $$('.view').forEach(v=>v.classList.remove('active-view'));
  const target=$(`#view-${route}`); if(target) target.classList.add('active-view');
  $$('.nav-item').forEach(item=>item.classList.toggle('active',item.dataset.route===route));
  const labels={dashboard:'Vue d’ensemble',parcours:'Mon parcours',lab:'Atelier DAX',ressources:'Ressources',notes:'Mes notes',lesson:'Leçon'};
  $('#breadcrumb-current').textContent=labels[route]||'Formation Power BI';
  if(route==='parcours') renderPath();
  if(route==='lab') renderLab();
  if(route==='ressources') renderGlossary();
  if(route==='notes') renderNotes();
  window.scrollTo({top:0,behavior:'smooth'});
  $('#sidebar').classList.remove('open');
}
let lastRouteKey=null;
const validRoutes=['dashboard','parcours','lab','ressources','notes'];
function applyRouteKey(key){
  if(key.startsWith('section-')) return; // ancre interne de lecon : on ne change pas de vue
  if(key.startsWith('module/')){
    const m=modules.find(x=>x.id===Number(key.split('/')[1]));
    if(m&&isUnlocked(m)){ currentModule=m.id; localStorage.setItem('nexora-current',m.id); renderLesson(m); navigateView('lesson'); return; }
    showToast('Ce module est indisponible ou encore verrouillé.');
    navigateView('dashboard'); return;
  }
  navigateView(validRoutes.includes(key)?key:'dashboard');
}
function setRouteKey(key){
  lastRouteKey=key;
  if((location.hash||'').replace(/^#\/?/,'')!==key) location.hash='#'+key;
  applyRouteKey(key);
}
function applyLocation(){
  const key=(location.hash||'').replace(/^#\/?/,'')||'dashboard';
  if(key.startsWith('section-')) return; // lien d'ancre : ni rendu ni changement de cle
  if(key===lastRouteKey) return;
  lastRouteKey=key;
  applyRouteKey(key);
}
window.addEventListener('hashchange',applyLocation);

function navigate(route){ setRouteKey(String(route)); }

function openModule(id){
  const m=getModule(id); if(!isUnlocked(m)){showToast('Terminez le module précédent pour déverrouiller celui-ci.');return;}
  currentModule=m.id; localStorage.setItem('nexora-current',m.id); setRouteKey('module/'+m.id);
}
function renderLesson(m){
  $('#lesson-header-module').textContent=`MODULE ${String(m.id).padStart(2,'0')}`; $('#lesson-header-time').textContent=m.time.toUpperCase(); $('#lesson-eyebrow').textContent=`MODULE ${String(m.id).padStart(2,'0')} · ${m.kicker}`; $('#lesson-title').textContent=m.title; $('#lesson-subtitle').textContent=m.subtitle;
  $('#complete-lesson').innerHTML=completedModules.includes(m.id)?'Module terminé <span>✓</span>':'Marquer comme terminé <span>✓</span>';
  const section=(title,body)=>`<h2>${title}</h2>${body}`;
  let html=`${section('Objectifs',`<ul>${m.objectives.map(x=>`<li>${x}</li>`).join('')}</ul>`)}<div class="tip-box"><strong>Prérequis :</strong> ${m.prereq}</div>${m.content}`;
  html+=`<h2>Démonstration pratique</h2><div class="demo-card"><div class="demo-head"><span class="demo-step">▶</span><strong>${m.demo.title}</strong></div><ol>${m.demo.steps.map(x=>`<li>${x}</li>`).join('')}</ol><div class="tip-box"><strong>Résultat attendu :</strong> ${m.demo.result}</div></div>`;
  html+=`<h2>Formule ou méthode clé</h2><div class="formula-box"><div class="formula-label">À RETENIR</div><code>${m.formula.code}</code><p><strong>${m.formula.name}</strong> — ${m.formula.explanation}</p></div>`;
  html+=`<h2>Erreurs fréquentes</h2><div class="warning-box"><ul>${m.errors.map(x=>`<li>${x}</li>`).join('')}</ul></div>`;
  html+=`<h2>Bonnes pratiques</h2><ul>${m.best.map(x=>`<li>${x}</li>`).join('')}</ul>`;
  html+=`<h2>Exercices</h2><div class="exercise-card"><h3>Exercice guidé</h3><p>${m.guided}</p><details><summary>Ouvrir les indications</summary><p>Avancez une étape à la fois, notez le résultat observé et comparez-le à la source. Si un résultat semble faux, revenez au type de données, au modèle puis au contexte de filtre.</p></details></div><div class="exercise-card" style="background:#fff;border-color:var(--line)"><h3 style="color:var(--ink)">Exercice autonome</h3><p>${m.autonomous}</p><details><summary>Voir la correction</summary><p>${m.correction}</p></details></div>`;
  html+=renderQuiz(m);
  html+=`<div class="mini-project"><p class="eyebrow">MINI-PROJET DU MODULE</p><h3>${m.project}</h3><p>Conservez votre livrable dans un dossier projet avec une convention de nommage et une note de contrôle. Vous pourrez le réutiliser dans votre portfolio.</p></div>`;
  $('#lesson-article').innerHTML=html;
  const headings=$$('h2', $('#lesson-article')); $('#lesson-toc-links').innerHTML=headings.map((h,i)=>`<a class="toc-link" href="#section-${i}" data-goto="section-${i}">${h.textContent}</a>`).join(''); headings.forEach((h,i)=>h.id=`section-${i}`);
}
function completeCurrent(){
  if(!completedModules.includes(currentModule)){ completedModules.push(currentModule); logActivity(1); completedModules.sort((a,b)=>a-b); localStorage.setItem('nexora-completed',JSON.stringify(completedModules)); showToast('Module validé — bravo, votre progression est enregistrée.'); }
  updateProgressUI(); renderLesson(getModule(currentModule));
}

function renderLab(){
  $('#formula-list').innerHTML=formulas.map((f,i)=>`<div class="formula-item ${i===selectedFormula?'active':''}" data-formula="${i}"><strong>${f.name}</strong><small>${f.tag}</small></div>`).join('');
  const f=formulas[selectedFormula]; $('#formula-detail').innerHTML=`<p class="eyebrow">FONCTION DAX · ${f.tag.toUpperCase()}</p><h2>${f.name}</h2><p>${f.description}</p><div class="code-editor"><span class="var">${f.code.split('=')[0]}=</span><br><span class="fn">${f.code.includes('=')?f.code.split('=').slice(1).join('=').trim():f.code}</span></div><div class="formula-result"><span class="result-number">${f.result}</span><small>Résultat simulé sur le jeu Contoso<br>selon le contexte courant</small></div><div class="tip-box" style="margin-top:22px"><strong>Quand l’utiliser :</strong> ${f.use}<br><strong>Vigilance :</strong> ${f.error}</div>`;
}
function renderGlossary(query=''){
  const result=glossary.filter(item=>item.t.toLowerCase().includes(query.toLowerCase()));
  $('#glossary-terms').innerHTML=result.map(item=>`<button class="glossary-term" data-term="${item.t}">${item.t}</button>`).join('')||'<small style="color:var(--muted)">Aucun terme trouvé.</small>';
  $('#glossary-count').textContent=`${glossary.length} termes`;
}
function showTermDefinition(term){
  const item=glossary.find(x=>x.t===term); if(!item) return;
  $$('.glossary-term').forEach(b=>b.classList.toggle('active',b.dataset.term===term));
  $('#glossary-definition').innerHTML=`<strong>${item.t}</strong><p>${item.d}</p>`;
}
function renderNotes(){
  const notes=JSON.parse(localStorage.getItem('nexora-notes')||'[]'); $('#saved-notes').innerHTML=notes.length?notes.map((n,i)=>`<div class="saved-note"><button class="delete-note" data-note="${i}" aria-label="Supprimer la note">×</button><p>${escapeHtml(n.text)}</p><small>${n.date}</small></div>`).join(''):'<div class="saved-note" style="grid-column:1/-1;background:#fff"><p style="color:var(--muted)">Aucune note pour le moment. Ajoutez votre première idée après une leçon.</p></div>';
}
function escapeHtml(text){return text.replace(/[&<>'"]/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#039;','"':'&quot;'}[c]));}
function downloadDataset(path='data/contoso_exercice.csv'){
  const fallbackContoso='DateVente,IDProduit,Produit,Categorie,Region,IDClient,Quantite,Montant\n2026-01-05,P-001,Casque Studio,Audio,Nord,C-102,2,159.80\n2026-01-08,P-004,Clavier Meca,Accessoires,Est,C-087,1,89.00\n2026-02-14,P-002,Enceinte Nomade,Audio,Sud,C-215,3,299.70\n2026-03-02,P-005,Webcam HD,Video,Ouest,C-102,1,74.90\n2026-03-17,P-003,Micro USB,Audio,Nord,C-331,2,119.80\n2026-04-06,P-004,Clavier Meca,Accessoires,Est,C-087,2,178.00\n2026-05-21,P-006,Souris Ergo,Accessoires,Sud,C-451,4,196.00\n2026-06-11,P-001,Casque Studio,Audio,Ouest,C-215,1,79.90';
  const name=String(path).split('/').pop();
  const save=(text,filename)=>{const blob=new Blob([text],{type:'text/csv;charset=utf-8'});const link=document.createElement('a');link.href=URL.createObjectURL(blob);link.download=filename;link.click();URL.revokeObjectURL(link.href);};
  fetch(path).then(r=>{if(!r.ok)throw 0;return r.text();}).then(t=>{save(t,name);showToast(`Fichier téléchargé : ${name}`);}).catch(()=>{
    if(path==='data/contoso_exercice.csv'){ save(fallbackContoso,'nexora_contoso_exercice.csv'); showToast('Jeu de données téléchargé (version embarquée).'); }
    else showToast(`Téléchargement indisponible : ${name}`);
  });
}
const checklistItems = [
  'Le besoin, le public et la décision à éclairer sont écrits.',
  'Chaque colonne possède le bon type de données.',
  'Les doublons, valeurs nulles et erreurs ont été traités.',
  'La granularité de la table de faits est connue et documentée.',
  'Le modèle est en étoile et les relations sont testées.',
  'Les mesures sont nommées, formatées et réutilisées.',
  'Les totaux principaux ont été rapprochés d’une source.',
  'Les titres portent un message, pas seulement un mot.',
  'Les unités, dates et filtres actifs sont visibles.',
  'Les couleurs ne sont pas le seul support d’information.',
  'Le rapport reste lisible sur une fenêtre plus petite.',
  'Une navigation claire existe entre les pages.',
  'La page À propos indique source, propriétaire et actualisation.',
  'Les rôles et accès ont été testés avec un compte lecteur (pas administrateur).',
  'L’actualisation est planifiée et son échec est surveillé.',
  'Aucune donnée personnelle réelle n’apparaît dans les captures.',
  'Le nom du rapport et du fichier .pbix sont cohérents et versionnés.',
  'Une reprise métier a validé le rapport avant la mise en ligne.'
];
function openChecklist(){
  $('#modal-content').innerHTML=`<p class="eyebrow">CHECK-LIST · 18 POINTS</p><h2 id="modal-title">Avant de publier un dashboard</h2><ul class="checklist-list">${checklistItems.map(x=>`<li>${x}</li>`).join('')}</ul>`;
  showModal();
}
function closeModal(){ const o=$('#modal-overlay'); if(o) o.hidden=true; document.body.classList.remove('modal-open'); }
function handleSearch(value){
  const q=value.trim().toLowerCase(); if(!q){renderDashboardModules();renderPath();return;} const matches=modules.filter(m=>[m.title,m.short,m.kicker,...m.objectives].join(' ').toLowerCase().includes(q)); renderDashboardModules(matches);renderPath(matches);
}
function renderSearchResults(raw){
  const box=$('#search-results'); if(!box) return;
  const q=raw.trim().toLowerCase();
  if(q.length<2){ closeSearchResults(); return; }
  const mods=modules.filter(m=>[m.title,m.short,m.kicker,...m.objectives].join(' ').toLowerCase().includes(q)).slice(0,5);
  const terms=glossary.filter(g=>(g.t+' '+g.d).toLowerCase().includes(q)).slice(0,5);
  const fs=formulas.filter(f=>(f.name+' '+f.code+' '+f.tag+' DAX').toLowerCase().includes(q)).slice(0,5);
  let html='';
  if(mods.length) html+='<p class="sr-group">MODULES</p>'+mods.map(m=>`<button class="sr-item" data-sr="module" data-id="${m.id}"><b>${String(m.id).padStart(2,'0')}</b><span>${m.title}</span><small>◷ ${m.time}</small></button>`).join('');
  if(terms.length) html+='<p class="sr-group">LEXIQUE</p>'+terms.map(t=>`<button class="sr-item" data-sr="term"><span>${t.t}</span></button>`).join('');
  if(fs.length) html+='<p class="sr-group">DAX</p>'+fs.map(f=>`<button class="sr-item" data-sr="formula" data-idx="${formulas.indexOf(f)}"><code>${f.name}</code><small>${f.tag}</small></button>`).join('');
  box.innerHTML=html||'<p class="sr-empty">Aucun résultat. Essayez « CALCULATE », « étoile » ou « DAX ».</p>';
  box.hidden=false;
}
function closeSearchResults(){ const b=$('#search-results'); if(b){ b.hidden=true; b.innerHTML=''; } }
function handleSearchResult(btn){
  const kind=btn.dataset.sr;
  closeSearchResults();
  if(kind==='module'){ openModule(Number(btn.dataset.id)); return; }
  if(kind==='term'){ const t=btn.querySelector('span')?.textContent||''; navigate('ressources'); showTermDefinition(t); const def=$('#glossary-definition'); if(def&&typeof def.scrollIntoView==='function') def.scrollIntoView({behavior:'smooth',block:'nearest'}); return; }
  if(kind==='formula'){ selectedFormula=Number(btn.dataset.idx); navigate('lab'); }
}

// Navigation and delegated interactions
$$('.nav-item').forEach(btn=>btn.addEventListener('click',()=>navigate(btn.dataset.route)));
$$('[data-route]').forEach(btn=>{if(!btn.classList.contains('nav-item')) btn.addEventListener('click',()=>navigate(btn.dataset.route));});
$('#mobile-menu').addEventListener('click',()=>$('#sidebar').classList.toggle('open'));
document.addEventListener('click',e=>{const sb=$('#sidebar');if(sb.classList.contains('open')&&!e.target.closest('#sidebar')&&!e.target.closest('#mobile-menu'))sb.classList.remove('open');});
$('#search-input').addEventListener('input',e=>{ const v=e.target.value; renderSearchResults(v); if(!v.trim()) handleSearch(''); });
$('#search-input').addEventListener('keydown',e=>{if(e.key==='Enter'){handleSearch(e.target.value); navigate('parcours'); closeSearchResults();}});
document.addEventListener('keydown',e=>{if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==='k'){e.preventDefault();$('#search-input').focus();}});
document.addEventListener('click',e=>{
  const card=e.target.closest('[data-module]'); if(card && !e.target.closest('.play-button,button[data-route]')) openModule(card.dataset.module);
  const play=e.target.closest('.play-button'); if(play) openModule(play.dataset.module);
  const formula=e.target.closest('[data-formula]'); if(formula){selectedFormula=Number(formula.dataset.formula);renderLab();}
  const goto=e.target.closest('[data-goto]'); if(goto){ e.preventDefault(); const el=document.getElementById(goto.dataset.goto); if(el&&typeof el.scrollIntoView==='function') el.scrollIntoView({behavior:'smooth',block:'start'}); }
  const sr=e.target.closest('[data-sr]'); if(sr){ handleSearchResult(sr); return; }
  if(e.target.closest('#reset-quiz')){ saveQuiz(currentModule,[]); renderLesson(getModule(currentModule)); showToast('Quiz réinitialisé — répondez à nouveau.'); return; }
  if(!e.target.closest('.topbar-search')) closeSearchResults();
  const qchoice=e.target.closest('[data-quiz-choice]'); if(qchoice&&!qchoice.disabled) handleQuizChoice(qchoice);
  const answer=e.target.closest('[data-answer]'); if(answer){const good=answer.dataset.answer==='right';$('#challenge-feedback').textContent=good?'✓ Exact. Une mesure respecte le contexte et se recalcule avec la période.':'À revoir : pensez à un calcul dynamique qui répond aux filtres du rapport.';$('#challenge-feedback').style.color=good?'var(--green)':'var(--coral)';}
  const term=e.target.closest('[data-term]'); if(term) showTermDefinition(term.dataset.term);
  const del=e.target.closest('[data-note]'); if(del){const notes=JSON.parse(localStorage.getItem('nexora-notes')||'[]');notes.splice(Number(del.dataset.note),1);localStorage.setItem('nexora-notes',JSON.stringify(notes));renderNotes();showToast('Note supprimée.');}
});
$('#complete-lesson').addEventListener('click',completeCurrent);
document.addEventListener('click',e=>{const dl=e.target.closest('[data-download]');if(dl)downloadDataset(dl.dataset.download);});
$('#glossary-input').addEventListener('input',e=>renderGlossary(e.target.value));
$('#checklist-button').addEventListener('click',openChecklist);
$('#modal-close').addEventListener('click',closeModal);
$('#modal-overlay').addEventListener('click',e=>{if(e.target===$('#modal-overlay'))closeModal();});
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeModal();});
$('#save-note').addEventListener('click',()=>{const text=$('#note-text').value.trim();if(!text){showToast('Écrivez une note avant de l’enregistrer.');return;}const notes=JSON.parse(localStorage.getItem('nexora-notes')||'[]');notes.unshift({text,date:new Intl.DateTimeFormat('fr-FR',{dateStyle:'medium'}).format(new Date())});localStorage.setItem('nexora-notes',JSON.stringify(notes));$('#note-text').value='';renderNotes();logActivity(1);showToast('Note enregistrée dans votre carnet.');});
$('#rename-profile').addEventListener('click',renameProfile);
$('#open-certificate').addEventListener('click',openCertificate);
$('#export-progress').addEventListener('click',exportProgress);
$('#import-progress').addEventListener('change',e=>{if(e.target.files[0])importProgress(e.target.files[0]);e.target.value='';});
$('#add-note').addEventListener('click',()=>{$('#note-text').focus();});
$('#export-notes').addEventListener('click',()=>{
  const notes=JSON.parse(localStorage.getItem('nexora-notes')||'[]');
  if(!notes.length){ showToast('Aucune note à exporter pour le moment.'); return; }
  const md='# Mes notes — NEXORA\n\n'+notes.map(n=>`## ${n.date}\n\n${n.text}\n`).join('\n---\n\n');
  try{
    const blob=new Blob([md],{type:'text/markdown;charset=utf-8'});
    const link=document.createElement('a'); link.href=URL.createObjectURL(blob); link.download='nexora_notes.md'; link.click(); URL.revokeObjectURL(link.href);
    showToast(`${notes.length} note${notes.length>1?'s':''} exportée${notes.length>1?'s':''} en Markdown.`);
  }catch(e){ showToast('Export impossible dans ce navigateur.'); }
});
$$('[data-action="start"],[data-action="continue"]').forEach(btn=>btn.addEventListener('click',()=>openModule(currentModule)));

// Initial render
const dateEl=$('#dashboard-date');
if(dateEl) dateEl.innerHTML=`${new Intl.DateTimeFormat('fr-FR',{weekday:'long',day:'numeric',month:'long',year:'numeric'}).format(new Date()).toUpperCase()} <span class="dot"></span> BON RETOUR`;
const labCount=$('#lab-function-count'); if(labCount) labCount.textContent=`${formulas.length} fonctions clés`;
applyName(); renderActivity(); renderDashboardModules(); renderPath(); updateProgressUI(); renderGlossary(); renderNotes();
applyLocation();
