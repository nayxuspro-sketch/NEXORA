# NEXORA - Guide Complet de Déploiement & Infrastructure

Ce guide détaille les procédures pour déployer l'application **NEXORA (ERP & POS)** dans tous les environnements, du simple poste de développement jusqu'au serveur VPS de production.

---

## 1. Vue d'ensemble des 3 Modes de Déploiement

| Mode | Cible | Composants | Complexité |
| :--- | :--- | :--- | :---: |
| **Mode 1 : Local Simple** | Développeur débutant, test rapide, démo hors-ligne | Python 3.11+, Django, SQLite3 | ⭐ (1 clic) |
| **Mode 2 : Local Professionnel** | Développeur avancé, staging local | Python, PostgreSQL 16, Redis, Next.js | ⭐⭐ |
| **Mode 3 : Docker Conteneurisé** | Production, VPS Cloud, Kubernetes | Docker Compose (PostgreSQL, Redis, Backend Gunicorn, Frontend Next.js) | ⭐⭐⭐ |

---

## 2. Déploiement sur Serveur Linux / VPS (Ubuntu / Debian)

### Étape 1 : Préparation du système hôte
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-venv python3-pip git curl nginx postgresql postgresql-contrib redis-server
```

### Étape 2 : Configuration de la Base PostgreSQL
```bash
sudo -u postgres psql
```
Dans l'invite PostgreSQL :
```sql
CREATE DATABASE nexora_db;
CREATE USER nexora WITH PASSWORD 'VOTRE_MOT_DE_PASSE_SECURISE';
ALTER ROLE nexora SET client_encoding TO 'utf8';
ALTER ROLE nexora SET default_transaction_isolation TO 'read committed';
ALTER ROLE nexora SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE nexora_db TO nexora;
\q
```

### Étape 3 : Déploiement de l'Application
```bash
git clone https://github.com/nayxuspro-sketch/NEXORA.git /var/www/nexora
cd /var/www/nexora
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt gunicorn
cp .env.example .env
# Renseigner les variables dans .env (DB_ENGINE=postgresql, etc.)
python manage.py migrate
python manage.py collectstatic --noinput
```

### Étape 4 : Service Systemd (`/etc/systemd/system/nexora-backend.service`)
```ini
[Unit]
Description=NEXORA Backend Gunicorn Service
After=network.target postgresql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/nexora
ExecStart=/var/www/nexora/.venv/bin/gunicorn --workers 4 --bind 127.0.0.1:8000 config.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

Activez et démarrez le service :
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now nexora-backend
```

### Étape 5 : Reverse Proxy Nginx & SSL Certbot
```nginx
server {
    listen 80;
    server_name erp.votre-domaine.com;

    location / {
        proxy_pass http://127.0.0.1:3000; # Frontend Next.js
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000; # Backend Django
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /static/ {
        alias /var/www/nexora/staticfiles/;
    }
}
```
Activez le certificat HTTPS gratuit avec Let's Encrypt :
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d erp.votre-domaine.com
```

---

## 3. Déploiement sur Windows

Pour exécuter en production sous Windows Server :
1. Installez Python 3.11 et PostgreSQL pour Windows.
2. Configurez le service Windows avec NSSM (Non-Sucking Service Manager) pour faire tourner `gunicorn` (ou `waitress`).
3. Pour le développement rapide, utilisez directement le script fourni `start-local.bat`.

---

## 4. Surveillance & Santé des Services (Healthcheck)

NEXORA expose un endpoint dédié pour les sondes de monitoring (Datadog, UptimeRobot, Docker, Kubernetes) :
- **URL** : `GET /api/v1/health/`
- **Code 200 OK** :
```json
{
  "status": "healthy",
  "timestamp": "2026-09-19T14:30:00Z",
  "version": "1.0.0",
  "database": "connected",
  "environment": "production"
}
```
- En cas de perte de connectivité avec la base de données, l'endpoint renvoie automatiquement le code `503 Service Unavailable`.
