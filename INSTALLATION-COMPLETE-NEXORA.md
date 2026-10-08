# Installation de NEXORA — archive complète

Cette archive réunit le code source de l’application fourni depuis `C:\NEXORA` et les correctifs intégrés, dont le bilan PDF vendeur sans plafond de produits. Ce n’est pas un exécutable `.exe` ou `.msi` : elle contient l’application complète à installer avec Python et Node.js.

## Contenu et données

- Backend Django, API, modèles et migrations.
- Interface Next.js, tests et documentation.
- Correctifs métier présents dans la source fournie, plus le correctif v2 du bilan vendeur.
- **Aucune base de données, aucun fichier `.env`, aucune sauvegarde ni donnée client** n’est incluse. La première installation initialise une base SQLite vide. Pour transférer des données existantes, utiliser séparément une sauvegarde/restauration validée.

## Prérequis Windows

- Windows 10/11.
- Python 3.11 ou supérieur, avec `py` dans le PATH.
- Node.js 20 LTS ou supérieur, avec `npm` dans le PATH.
- Environ 2 Go d’espace libre pour les dépendances de développement.

## Préparation — à faire une seule fois

1. Extraire le dossier `NEXORA-COMPLET` à l’emplacement voulu, par exemple `C:\NEXORA`.
2. Ouvrir **Invite de commandes** dans ce dossier et exécuter :

```bat
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe manage.py migrate
.venv\Scripts\python.exe manage.py createsuperuser
cd frontend
npm ci
```

La dernière commande de création de compte demande les informations du premier administrateur local. Ne communiquez jamais son mot de passe.

## Démarrage local

Lancer deux fenêtres d’Invite de commandes et les laisser ouvertes.

**Fenêtre 1 — backend**, depuis `C:\NEXORA` (adapter le chemin si l’archive est extraite ailleurs) :

```bat
.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8008
```

**Fenêtre 2 — interface**, depuis `C:\NEXORA\frontend` :

```bat
if not exist .env.local echo NEXT_PUBLIC_API_URL=http://127.0.0.1:8008/api/v1>.env.local
npm run dev
```

Ouvrir ensuite `http://localhost:3000`. Le backend local est sur `http://127.0.0.1:8008`.

Après cette préparation initiale, vous pouvez aussi lancer `start-local.bat` depuis la racine : il vérifie la présence de `.venv` et des dépendances frontend, puis ouvre deux fenêtres de serveur. Il ne lance pas les migrations et ne crée pas le compte administrateur ; ces étapes se font une fois ci-dessus.

## Vérification après installation

Depuis la racine du projet :

```bat
.venv\Scripts\python.exe manage.py check
.venv\Scripts\python.exe manage.py test
```

Les tests utilisent une base temporaire ; ils ne remplacent pas une sauvegarde et ne migrent pas une base de production.

## Important pour un déploiement en production

Cette procédure lance un environnement local de développement. Ne publiez pas ce serveur sur Internet et ne réutilisez pas la configuration locale en production. Pour PostgreSQL, HTTPS, les variables de secrets, les hôtes autorisés, les sauvegardes et le déploiement serveur, suivre `DEPLOYMENT.md` et `SECURITY_CHECKLIST.md`, puis effectuer une recette sur une base de test séparée. L’archive ne transfère ni les données ni les identifiants de votre poste actuel.
