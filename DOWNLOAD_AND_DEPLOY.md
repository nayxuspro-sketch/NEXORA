# NEXORA - Guide de Téléchargement & Déploiement Prêt à l'Emploi

Voici toutes les options pour récupérer et déployer l'application **NEXORA** sur votre machine ou votre serveur.

---

## Option 1 : Téléchargement Direct via Archive (Recommandé)

Deux archives autonomes (sans fichiers inutiles, ni `.git`, ni `node_modules` volumineux) sont générées et prêtes à l'emploi à la racine du projet :

- **Format ZIP (Windows / Universel)** :
  `nexora-release-v1.0.0.zip` (Taille : ~260 Ko)
- **Format TAR.GZ (Linux / macOS / Serveurs)** :
  `nexora-release-v1.0.0.tar.gz` (Taille : ~360 Ko)

### Pour extraire l'archive :
```bash
# Sous Windows : Clic droit > Extraire tout, ou :
tar -xf nexora-release-v1.0.0.zip

# Sous Linux / macOS :
tar -xzf nexora-release-v1.0.0.tar.gz
cd NEXORA
```

---

## Option 2 : Téléchargement via Git / GitHub

Le projet complet est déjà synchronisé sur GitHub sur votre branche officielle :

```bash
git clone -b arena/01a0ba27-nexora https://github.com/nayxuspro-sketch/NEXORA.git
cd NEXORA
```

---

## Déploiement en 1 Clic sur votre Ordinateur

Une fois l'application extraite, choisissez votre mode de déploiement :

### 1. Sous Windows (Mode débutant en 1 clic)
Double-cliquez simplement sur :
```
start-local.bat
```
*Le script configure l'environnement virtuel, installe les dépendances, initialise la base SQLite3 et lance le serveur.*

### 2. Sous Linux / macOS (Mode débutant en 1 commande)
Ouvrez votre terminal dans le dossier et lancez :
```bash
./start-local.sh
```

### 3. Avec Docker & Docker Compose (Mode professionnel / Production)
Pour lancer la stack conteneurisée complète (PostgreSQL 16, Redis 7, Backend Django Gunicorn, Frontend Next.js) :
```bash
cp .env.example .env
docker compose up -d --build
```

---

## Accès aux Services une fois Démarré

- **Interface Frontend & Point de Vente** : [http://localhost:3000](http://localhost:3000)
- **Backend API & Swagger OpenAPI** : [http://localhost:8000/api/v1/docs/](http://localhost:8000/api/v1/docs/)
- **Administration Django** : [http://localhost:8000/admin/](http://localhost:8000/admin/)
- **Sonde de Santé** : [http://localhost:8000/api/v1/health/](http://localhost:8000/api/v1/health/)

### Identifiants Administrateur Démo :
- **Email** : `admin@nexora-enterprise.com`
- **Mot de passe** : `Password123!`
