#!/usr/bin/env bash
# ==============================================================================
# NEXORA - Script de Sauvegarde de Base de Données (PostgreSQL ou SQLite3)
# ==============================================================================

set -e

BACKUP_DIR="${BACKUP_DIR:-./backups}"
mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DB_ENGINE="${DB_ENGINE:-sqlite}"

if [ "$DB_ENGINE" = "postgresql" ]; then
    BACKUP_FILE="${BACKUP_DIR}/nexora_backup_postgres_${TIMESTAMP}.sql.gz"
    echo "[SAUVEGARDE] Démarrage de la sauvegarde PostgreSQL vers ${BACKUP_FILE}..."

    PGPASSWORD="${DB_PASSWORD:-nexora_secret}" pg_dump \
        -h "${DB_HOST:-localhost}" \
        -p "${DB_PORT:-5432}" \
        -U "${DB_USER:-nexora}" \
        -d "${DB_NAME:-nexora_db}" \
        --clean --if-exists | gzip > "$BACKUP_FILE"

    echo "[SUCCÈS] Sauvegarde PostgreSQL effectuée : $(ls -lh "$BACKUP_FILE")"

else
    BACKUP_FILE="${BACKUP_DIR}/nexora_backup_sqlite_${TIMESTAMP}.db"
    echo "[SAUVEGARDE] Démarrage de la sauvegarde SQLite3 vers ${BACKUP_FILE}..."

    if [ -f "db.sqlite3" ]; then
        sqlite3 db.sqlite3 ".backup '${BACKUP_FILE}'"
        echo "[SUCCÈS] Sauvegarde SQLite3 effectuée : $(ls -lh "$BACKUP_FILE")"
    else
        echo "[AVERTISSEMENT] Aucune base db.sqlite3 trouvée dans le répertoire courant."
        exit 1
    fi
fi
