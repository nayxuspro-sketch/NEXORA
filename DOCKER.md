# NEXORA - Déploiement Conteneurisé avec Docker & Docker Compose

Ce guide explique comment lancer la stack complète **NEXORA** (PostgreSQL 16, Redis 7, Backend Django REST et Frontend Next.js) via Docker en une seule commande.

---

## 1. Prérequis

- [Docker Engine](https://docs.docker.com/engine/install/) (v24.0+)
- [Docker Compose](https://docs.docker.com/compose/install/) (v2.20+)

---

## 2. Architecture des Conteneurs

```
┌─────────────────────────────────────────────────────────────┐
│                       NEXORA STACK                          │
│                                                             │
│   ┌──────────────┐     ┌──────────────┐    ┌────────────┐   │
│   │   Frontend   │     │   Backend    │    │ PostgreSQL │   │
│   │   Next.js    │────▶│ Django (DRF) │───▶│     16     │   │
│   │  Port 3000   │     │  Port 8000   │    │ Port 5432  │   │
│   └──────────────┘     └──────────────┘    └────────────┘   │
│                               │                             │
│                               ▼                             │
│                        ┌──────────────┐                     │
│                        │    Redis     │                     │
│                        │  Port 6379   │                     │
│                        └──────────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Lancement Rapide en Production

### Étape 1 : Cloner le dépôt et initialiser les variables
```bash
git clone https://github.com/nayxuspro-sketch/NEXORA.git
cd NEXORA
cp .env.example .env
```
Éditez le fichier `.env` pour définir un mot de passe fort pour PostgreSQL et une clé secrète Django.

### Étape 2 : Construire et démarrer les conteneurs
```bash
docker compose up -d --build
```

### Étape 3 : Vérifier l'état de santé des services
```bash
docker compose ps
```
Tous les conteneurs (`nexora-postgres`, `nexora-redis`, `nexora-backend`, `nexora-frontend`) doivent afficher le statut `Up (healthy)`.

---

## 4. Commandes d'Exploitation Docker Fréquentes

| Action | Commande Docker Compose |
| :--- | :--- |
| **Consulter les logs en direct** | `docker compose logs -f backend` |
| **Créer un super-administrateur** | `docker compose exec backend python manage.py createsuperuser` |
| **Exécuter les tests unitaires** | `docker compose exec backend python manage.py test tests` |
| **Appliquer une nouvelle migration** | `docker compose exec backend python manage.py migrate` |
| **Arrêter l'ensemble des services**| `docker compose down` |
| **Arrêter et supprimer les volumes** | `docker compose down -v` *(Attention : supprime les données)* |

---

## 5. Sauvegarde Automatisée dans Docker

Le volume de sauvegarde est monté dans `./backups/` :
```bash
docker compose exec postgres pg_dump -U nexora -d nexora_db | gzip > ./backups/docker_backup_$(date +%Y%m%d).sql.gz
```
