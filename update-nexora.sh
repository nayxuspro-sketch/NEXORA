#!/bin/bash
set -e

echo "====================================================================="
echo "          NEXORA Enterprise ERP - Script de Mise à Jour"
echo "====================================================================="
echo ""
echo "Ce script applique la mise à jour tout en préservant votre base de données."

if [ -f "db.sqlite3" ]; then
    BACKUP_NAME="db.sqlite3.backup-$(date +%Y%m%d_%H%M%S)"
    cp db.sqlite3 "$BACKUP_NAME"
    echo "✓ Sauvegarde de précaution effectuée : $BACKUP_NAME"
fi

echo "✓ Application des nouvelles migrations de base de données..."
python3 manage.py migrate

echo "✓ Mise à jour terminée avec succès !"
echo "Pour relancer NEXORA : ./start-local.sh"
