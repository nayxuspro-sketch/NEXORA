# NEXORA - Sauvegarde et Restauration des Données

Ce document décrit les procédures de sauvegarde, de restauration et de vérification d'intégrité des bases de données **SQLite3** et **PostgreSQL**.

---

## 1. Scripts Clés en Main

Deux scripts exécutables sont fournis à la racine du projet sous `scripts/` :
- `scripts/backup.sh` : Déclenche l'exportation horodatée et compressée de la base de données.
- `scripts/restore.sh` : Restaure une sauvegarde existante.

---

## 2. Procédure de Sauvegarde

### Mode SQLite3 (Environnement Local Simple)
```bash
./scripts/backup.sh
```
Le script crée une copie cohérente via l'API de backup en ligne de SQLite dans le répertoire `./backups/` :
`./backups/nexora_backup_sqlite_AAAA-MM-JJ_HHMMSS.db`

### Mode PostgreSQL (Production & Staging)
Définissez les variables d'environnement (ou laissez le script lire `.env`) :
```bash
export DB_ENGINE=postgresql
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=nexora_db
export DB_USER=nexora
export DB_PASSWORD=nexora_secret

./scripts/backup.sh
```
Fichier généré : `./backups/nexora_backup_postgres_AAAA-MM-JJ_HHMMSS.sql.gz`

---

## 3. Procédure de Restauration

### Restauration SQLite3 :
```bash
./scripts/restore.sh ./backups/nexora_backup_sqlite_20260919_120000.db
```

### Restauration PostgreSQL :
```bash
export DB_ENGINE=postgresql
./scripts/restore.sh ./backups/nexora_backup_postgres_20260919_120000.sql.gz
```

---

## 4. Vérification d'Intégrité Post-Restauration

Après toute restauration, validez immédiatement l'intégrité des données :
```bash
# 1. Vérifier la santé du backend et de la base
curl -s http://127.0.0.1:8000/api/v1/health/ | grep '"database": "connected"'

# 2. Exécuter la suite de tests de validation
python manage.py test tests
```

---

## 5. Automatisation Quotidienne (Cron Linux)

Pour planifier une sauvegarde automatique tous les soirs à 02h00 du matin :
```bash
crontab -e
```
Ajoutez la ligne :
```cron
0 2 * * * cd /var/www/nexora && ./scripts/backup.sh >> /var/log/nexora_backup.log 2>&1
```
