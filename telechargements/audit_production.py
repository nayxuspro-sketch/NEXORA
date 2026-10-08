# -*- coding: utf-8 -*-
"""Audit de production NEXORA.

Commande : py manage.py audit_production
Analyse reelle de l'installation :
  [1] base de donnees (moteur, fichier, connexions) ;
  [2] transactions de stock & caisse (analyse statique : atomic / select_for_update) ;
  [3] configuration production & securite (DEBUG, ALLOWED_HOSTS, CORS, SECRET_KEY,
      JWT, cookies securises, HSTS, statiques, journalisation, superusers) ;
  [4] sauvegardes presentes + volumes reels d'activite (7 jours).
Le rapport est aussi enregistre dans audit_production_<horodatage>.txt a la racine.
Sortie console compatible cp1252 (pas d'emoji, fleches '->').
"""

import datetime
import os
import re
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "Audit de production : base, transactions de stock, configuration, sauvegardes, volumes."

    def handle(self, *args, **options):
        base = Path(str(settings.BASE_DIR))
        now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        lignes = []
        add = lignes.append
        sep = "-" * 74

        add("=" * 74)
        add("RAPPORT D'AUDIT PRODUCTION - NEXORA   %s"
            % datetime.datetime.now().strftime("%d/%m/%Y %H:%M"))
        add("=" * 74)

        # ---------------- [1] BASE DE DONNEES ----------------
        add("")
        add("[1] BASE DE DONNEES")
        add(sep)
        db = settings.DATABASES["default"]
        engine = str(db.get("ENGINE", ""))
        add("  Moteur           : %s" % engine)
        add("  Nom / fichier    : %s" % db.get("NAME"))
        add("  CONN_MAX_AGE     : %s" % db.get("CONN_MAX_AGE", 0))
        add("  ATOMIC_REQUESTS  : %s" % db.get("ATOMIC_REQUESTS", False))
        if "sqlite3" in engine:
            p = Path(str(db.get("NAME")))
            taille = p.stat().st_size // 1024 if p.exists() else 0
            add("  [CRITIQUE] SQLite : ecritures serialisees -> 'database is locked'")
            add("               des 10-15 utilisateurs simultanes. PostgreSQL requis")
            add("               avant ouverture en magasin. Taille actuelle : %s Ko" % taille)
        elif "postgresql" in engine:
            add("  [OK] PostgreSQL : moteur adapte a 30 utilisateurs simultanes.")
        elif "mysql" in engine:
            add("  [OK] MySQL/MariaDB : acceptable a 30 utilisateurs (InnoDB requis).")
        else:
            add("  [ATTENTION] Moteur non evalue : %s" % engine)

        # ---------------- [2] TRANSACTIONS STOCK & CAISSE ----------------
        add("")
        add("[2] TRANSACTIONS DE STOCK & CAISSE (analyse statique du code)")
        add(sep)
        ecriture = re.compile(r"\.save\(|\.update\(|\.delete\(|F\(|bulk_update|bulk_create")
        cibles = re.compile(r"StockLevel|StockMovement|SaleItem|RegisterSession|Payment")
        vus = []
        for py in sorted(base.glob("apps/**/*.py")):
            if "migrations" in py.parts or "tests" in py.name:
                continue
            try:
                src = py.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if not cibles.search(src) or not ecriture.search(src):
                continue
            atom = "transaction.atomic" in src
            lock = "select_for_update" in src
            if atom and lock:
                etat = "[OK]        atomic + select_for_update"
            elif atom:
                etat = "[ATTENTION] atomic sans select_for_update (risque de course)"
            else:
                etat = "[CRITIQUE]  aucune transaction atomique detectee"
            add("  %-56s %s" % (str(py.relative_to(base)), etat))
            vus.append(etat)
        if not vus:
            add("  Aucun fichier d'ecriture stock/caisse trouve : verifier noms de modeles.")
        else:
            crit = sum(1 for e in vus if e.startswith("[CRITIQUE]"))
            part = sum(1 for e in vus if e.startswith("[ATTENTION]"))
            add("  Synthese : %s fichier(s) analysé(s) -> %s critique(s), %s a surveiller."
                % (len(vus), crit, part))

        # ---------------- [3] CONFIGURATION PRODUCTION ----------------
        add("")
        add("[3] CONFIGURATION PRODUCTION & SECURITE")
        add(sep)
        debug = getattr(settings, "DEBUG", None)
        add("  DEBUG                  : %s  %s"
            % (debug, "[OK]" if not debug else "[CRITIQUE] jamais en production"))
        hosts = list(getattr(settings, "ALLOWED_HOSTS", []) or [])
        if not debug and not hosts:
            add("  ALLOWED_HOSTS          : vide  [CRITIQUE] Django refusera les requetes")
        elif "*" in hosts:
            add("  ALLOWED_HOSTS          : ['*']  [ATTENTION] restreindre au domaine du magasin")
        else:
            add("  ALLOWED_HOSTS          : %s  [OK]" % hosts)
        cors_all = getattr(settings, "CORS_ALLOW_ALL_ORIGINS",
                           getattr(settings, "CORS_ORIGIN_ALLOW_ALL", False))
        origins = getattr(settings, "CORS_ALLOWED_ORIGINS",
                          getattr(settings, "CORS_ORIGIN_WHITELIST", None))
        if cors_all:
            add("  CORS                   : TOUTES origines  [CRITIQUE]")
        else:
            add("  CORS_ALLOWED_ORIGINS   : %s  [OK]" % (origins or "non defini"))

        src_settings = ""
        for cand in list(base.glob("settings.py")) + list(base.glob("*/settings.py")):
            try:
                src_settings += cand.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                pass
        m = re.search(r"SECRET_KEY\s*=\s*(.*)", src_settings)
        cle = getattr(settings, "SECRET_KEY", "")
        if m and re.search(r"environ|getenv|config\(", m.group(1)):
            add("  SECRET_KEY             : via variable d'environnement  [OK]")
        elif len(cle) >= 50:
            add("  SECRET_KEY             : %s car. mais verifier qu'elle n'est pas en dur  [ATTENTION]" % len(cle))
        else:
            add("  SECRET_KEY             : courte ou absente  [CRITIQUE]")

        jwt = getattr(settings, "SIMPLE_JWT", {}) or {}
        rot = bool(jwt.get("ROTATE_REFRESH_TOKENS", False))
        add("  JWT rotation refresh   : %s  %s" % (rot, "[OK]" if rot else "[ATTENTION]"))
        blacklist = "rest_framework_simplejwt.token_blacklist" in list(settings.INSTALLED_APPS)
        add("  JWT blacklist          : %s  %s"
            % (blacklist, "[OK]" if blacklist else "[ATTENTION] app token_blacklist absente"))
        for nom in ("SECURE_SSL_REDIRECT", "SESSION_COOKIE_SECURE", "CSRF_COOKIE_SECURE"):
            v = bool(getattr(settings, nom, False))
            add("  %-22s : %s  %s" % (nom, v, "[OK]" if v else "[ATTENTION] requis des que TLS active"))
        hsts = getattr(settings, "SECURE_HSTS_SECONDS", 0) or 0
        add("  SECURE_HSTS_SECONDS    : %s  %s" % (hsts, "[OK]" if hsts else "[ATTENTION]"))
        whitenoise = any("whitenoise" in x for x in list(settings.MIDDLEWARE) + list(settings.INSTALLED_APPS))
        add("  Whitenoise (statiques) : %s  %s"
            % (whitenoise, "[OK]" if whitenoise else "[ATTENTION] qui sert /static en production ?"))
        log_cfg = getattr(settings, "LOGGING", None) or {}
        ok_log = bool(log_cfg.get("handlers"))
        add("  LOGGING configure      : %s  %s" % (ok_log, "[OK]" if ok_log else "[ATTENTION]"))
        lang = getattr(settings, "LANGUAGE_CODE", "?")
        add("  LANGUAGE_CODE          : %s  %s" % (lang, "[OK]" if lang.lower().startswith("fr") else "[ATTENTION]"))

        from django.contrib.auth import get_user_model
        U = get_user_model()
        tot = U.objects.filter(is_active=True).count()
        su = U.objects.filter(is_superuser=True, is_active=True).count()
        add("  Utilisateurs actifs    : %s (dont %s superuser(s))" % (tot, su))

        # ---------------- [4] SAUVEGARDES & VOLUMES ----------------
        add("")
        add("[4] SAUVEGARDES & VOLUMES REELS")
        add(sep)
        sauvs = []
        for motif in ("*.dump", "*.bak", "*.sql", "*backup*.zip", "*sauvegarde*.zip"):
            sauvs += list(base.parent.glob(motif)) + list(base.glob(motif))
        seuil = datetime.datetime.now().timestamp() - 7 * 86400
        recentes = [p for p in sauvs if p.stat().st_mtime >= seuil]
        if sauvs:
            add("  Sauvegardes trouvees   : %s (dont %s de moins de 7 jours)  %s"
                % (len(sauvs), len(recentes), "[OK]" if recentes else "[CRITIQUE] aucune recente"))
        else:
            add("  Sauvegardes trouvees   : 0  [CRITIQUE] aucune strategie visible")

        def compte(app, modele, depuis=None):
            try:
                from django.apps import apps as django_apps
                M = django_apps.get_model(app, modele)
                qs = M.objects.all()
                if depuis is not None:
                    champ = next((c for c in ("created_at", "created", "date_created",
                                              "timestamp", "datetime", "date")
                                  if hasattr(M, c)), None)
                    if not champ:
                        return None
                    qs = qs.filter(**{champ + "__gte": depuis})
                return qs.count()
            except Exception:
                return None

        sept = timezone.now() - datetime.timedelta(days=7)
        add("  Ventes (7 j)           : %s" % compte("sales", "Sale", sept))
        add("  Lignes de vente (7 j)  : %s" % compte("sales", "SaleItem", sept))
        add("  Mouvements stock (7 j) : %s" % compte("inventory", "StockMovement", sept))
        add("  Sessions caisse (7 j)  : %s" % compte("pos", "RegisterSession", sept))
        add("  Journal d'audit (total): %s" % compte("audit", "AuditLog"))

        add("")
        add("=" * 74)
        add("Fin du rapport. Copie enregistree : audit_production_%s.txt" % now)
        add("=" * 74)

        for ligne in lignes:
            self.stdout.write(ligne)
        try:
            (base / ("audit_production_%s.txt" % now)).write_text(
                "\n".join(lignes), encoding="utf-8")
        except OSError:
            pass
