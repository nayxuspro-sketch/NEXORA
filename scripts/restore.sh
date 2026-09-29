#!/usr/bin/env bash
# ==============================================================================
# NEXORA - Script de Restauration de Base de Données
# Usage: ./scripts/restore.sh <chemin_du_fichier_de_sauvegarde>
# ==============================================================================

set -e

BACKUP_FILE="$1"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <chemin_vers_le_fichier_de_sauvegarde>"
    echo "Exemple SQLite : $0 ./backups/nexora_backup_sqlite_20260919_120000.db"
    echo "Exemple Postgres: $0 ./backups/nexora_backup_postgres_20260919_120000.sql.gz"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "[ERREUR] Le fichier $BACKUP_FILE n'existe pas."
    exit 1
fi

DB_ENGINE="${DB_ENGINE:-sqlite}"

if [ "$DB_ENGINE" = "postgresql" ]; then
    echo "[RESTAURATION] Restauration PostgreSQL depuis $BACKUP_FILE..."
    gunzip -c "$BACKUP_FILE" | PGPASSWORD="${DB_PASSWORD:-nexora_secret}" psql \
        -h "${DB_HOST:-localhost}" \
        -p "${DB_PORT:-5432}" \
        -U "${DB_USER:-nexora}" \
        -d "${DB_NAME:-nexora_db}"
    echo "[SUCCÈS] Restauration PostgreSQL terminée."
else
    echo "[RESTAURATION] Restauration SQLite3 depuis $BACKUP_FILE..."
    cp "$BACKUP_FILE" db.sqlite3
    echo "[SUCCÈS] Base db.sqlite3 restaurée avec succès."
fi
