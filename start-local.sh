#!/usr/bin/env bash
# ==============================================================================
# NEXORA ERP & POS - Démarrage Rapide Local Simple (Linux & macOS)
# Mode: Python + Django + SQLite3 (Zéro configuration externe requise)
# ==============================================================================

set -e

echo "=============================================================================="
echo "[NEXORA] Initialisation de l'environnement local simple (Linux/macOS)..."
echo "=============================================================================="

# 1. Vérification de l'installation de Python
if ! command -v python3 &> /dev/null; then
    echo "[ERREUR] Python 3 n'est pas installé."
    echo "Veuillez installer Python 3.11+ via votre gestionnaire de paquets (ex: apt install python3 python3-venv)"
    exit 1
fi

# 2. Création de l'environnement virtuel (.venv) si absent
if [ ! -d ".venv" ]; then
    echo "[1/5] Création de l'environnement virtuel Python..."
    python3 -m venv .venv
else
    echo "[1/5] Environnement virtuel existant détecté (.venv)."
fi

# 3. Activation de l'environnement virtuel
echo "[2/5] Activation de l'environnement virtuel..."
source .venv/bin/activate

# 4. Installation des dépendances backend
echo "[3/5] Installation / mise à jour des dépendances..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

# 5. Application des migrations de base de données (SQLite3 par défaut)
echo "[4/5] Application des migrations de base de données..."
python manage.py migrate

# 6. Démarrage du serveur Django
echo "=============================================================================="
echo "[5/5] Démarrage de NEXORA Backend sur http://127.0.0.1:8000"
echo "Documentation API Swagger : http://127.0.0.1:8000/api/v1/docs/"
echo "Vérification de santé (Healthcheck) : http://127.0.0.1:8000/api/v1/health/"
echo "Pour arrêter le serveur : Appuyez sur CTRL + C"
echo "=============================================================================="

python manage.py runserver 0.0.0.0:8000
