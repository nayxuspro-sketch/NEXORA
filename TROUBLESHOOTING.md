# NEXORA - Guide de Dépannage & Diagnostic (Troubleshooting)

Ce guide répertorie les erreurs fréquentes rencontrées lors de l'installation, du déploiement ou de l'exploitation de **NEXORA**, ainsi que leurs résolutions immédiates.

---

## 1. Problèmes d'Environnement & Dépendances

### Erreur : `externally-managed-environment` lors de l'installation pip
- **Cause** : Sous Debian 12 / Ubuntu 24.04 (PEP 668), l'installation globale sans environnement virtuel est bloquée par le système.
- **Solution** :
  Toujours utiliser un environnement virtuel :
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  ```

---

## 2. Base de Données & Migrations

### Erreur : `fe_sendauth: no password supplied` ou `Ident authentication failed for user "nexora"`
- **Cause** : Mauvaise configuration des droits d'accès dans PostgreSQL ou mot de passe manquant dans le fichier `.env`.
- **Solution** :
  1. Vérifiez que `pg_hba.conf` autorise la méthode `scram-sha-256` ou `md5` pour `127.0.0.1/32`.
  2. Assurez-vous que les variables `DB_USER` et `DB_PASSWORD` dans `.env` correspondent à celles de l'utilisateur PostgreSQL.

### Erreur : `sqlite3.OperationalError: no such table: ...`
- **Cause** : Les migrations Django n'ont pas encore été appliquées.
- **Solution** :
  ```bash
  python manage.py migrate
  ```

---

## 3. Réseau, CORS & Point de Vente

### Erreur : `Cross-Origin Request Blocked` (CORS) lors d'un appel API depuis le Frontend
- **Cause** : Le domaine ou port du frontend n'est pas autorisé par le middleware Django.
- **Solution** :
  Dans `config/settings.py`, `CORS_ALLOW_ALL_ORIGINS = True` est activé par défaut en développement. En production, renseignez vos domaines autorisés dans la variable `CORS_ALLOWED_ORIGINS` dans `.env`.

### Erreur : `503 Service Unavailable` sur `/api/v1/health/`
- **Cause** : Le serveur web Django tourne, mais la connexion à la base de données PostgreSQL a échoué.
- **Solution** :
  Vérifiez le statut du service de base de données :
  ```bash
  # Linux systemd
  sudo systemctl status postgresql

  # Docker Compose
  docker compose ps postgres
  ```

---

## 4. Frontend Next.js

### Erreur : `Module not found` ou erreur de compilation npm
- **Cause** : Dépendances manquantes ou cache corrompu.
- **Solution** :
  ```bash
  cd frontend
  rm -rf node_modules .next package-lock.json
  npm install
  npm run build
  ```

---

## 5. Journalisation des Erreurs (Logs)

Pour consulter les traces détaillées en cas de dysfonctionnement imprévu :
```bash
# Mode développement local
tail -f debug.log

# Mode Docker
docker compose logs -f backend

# Mode Linux systemd
sudo journalctl -u nexora-backend -f -n 100
```
