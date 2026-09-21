# NEXORA - Guide d'Installation Locale Simple (Débutant)

Ce guide est spécialement rédigé pour les développeurs ou utilisateurs débutants souhaitant lancer **NEXORA** sur leur ordinateur sans installer Docker ni PostgreSQL.

Le mode simple utilise **Python + Django + SQLite3** (base de données fichier autonome).

---

## 1. Méthode Automatique en 1 Clic

### Sous Windows :
Double-cliquez simplement sur le fichier :
```
start-local.bat
```
Ce script va automatiquement :
1. Détecter Python.
2. Créer l'environnement virtuel `.venv`.
3. Installer toutes les dépendances requises.
4. Créer et initialiser la base de données SQLite3.
5. Lancer le serveur Django sur `http://127.0.0.1:8000`.

### Sous Linux ou macOS :
Ouvrez un terminal dans le dossier du projet et exécutez :
```bash
./start-local.sh
```

---

## 2. Méthode Manuelle Étape par Étape

Si vous préférez exécuter les commandes une par une :

### Étape 1 : Installer Python
Assurez-vous que Python 3.11 ou supérieur est installé :
```bash
python3 --version
```

### Étape 2 : Créer et activer l'environnement virtuel
```bash
# Création
python3 -m venv .venv

# Activation (Linux / macOS)
source .venv/bin/activate

# Activation (Windows PowerShell)
.venv\Scripts\Activate.ps1
```

### Étape 3 : Installer les dépendances
```bash
pip install -r requirements.txt
```

### Étape 4 : Initialiser la base de données
```bash
python manage.py migrate
```

### Étape 5 : Créer votre premier compte Administrateur
```bash
python manage.py createsuperuser
```
*(Indiquez votre email et un mot de passe)*.

### Étape 6 : Démarrer le serveur
```bash
python manage.py runserver 0.0.0.0:8000
```

Accédez à :
- **Application Backend & Documentation API** : [http://127.0.0.1:8000/api/v1/docs/](http://127.0.0.1:8000/api/v1/docs/)
- **Administration Django** : [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)
- **Vérification de santé** : [http://127.0.0.1:8000/api/v1/health/](http://127.0.0.1:8000/api/v1/health/)

---

## 3. Lancer l'Interface Frontend (Next.js)

Dans un second terminal :
```bash
cd frontend
npm install
npm run dev
```
Ouvrez votre navigateur sur : [http://localhost:3000](http://localhost:3000)
