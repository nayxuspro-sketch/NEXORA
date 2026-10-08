# -*- coding: utf-8 -*-
"""Ajoute un profil de production dormant, valide et reversible a config/settings.py."""

import ast
import os
import sys
from datetime import datetime
from pathlib import Path

MARKER = "# NEXORA_PRODUCTION_PROFILE_V1"

PROFILE = r'''# NEXORA_PRODUCTION_PROFILE_V1
# Ce profil ne s'active que si NEXORA_ENVIRONMENT=production.
import os as _nexora_os
from datetime import timedelta as _nexora_timedelta
from urllib.parse import urlsplit as _nexora_urlsplit
from django.core.exceptions import ImproperlyConfigured as _NexoraImproperlyConfigured

_nexora_mode = _nexora_os.environ.get("NEXORA_ENVIRONMENT", "development").strip().lower()
if _nexora_mode not in ("development", "production"):
    raise _NexoraImproperlyConfigured("NEXORA_ENVIRONMENT doit valoir development ou production.")

if _nexora_mode == "production":
    DEBUG = False

    _nexora_hosts = list(dict.fromkeys(
        item.strip() for item in _nexora_os.environ.get("NEXORA_ALLOWED_HOSTS", "").split(",") if item.strip()
    ))
    if not _nexora_hosts or "*" in _nexora_hosts:
        raise _NexoraImproperlyConfigured("Definissez NEXORA_ALLOWED_HOSTS avec les noms/IP exacts, sans joker.")
    if any("://" in item or "/" in item for item in _nexora_hosts):
        raise _NexoraImproperlyConfigured("NEXORA_ALLOWED_HOSTS contient des hotes, sans schema URL ni chemin.")
    ALLOWED_HOSTS = _nexora_hosts

    def _nexora_csv(name):
        return list(dict.fromkeys(
            item.strip() for item in _nexora_os.environ.get(name, "").split(",") if item.strip()
        ))

    def _nexora_validate_https_origins(name, values):
        for value in values:
            parsed = _nexora_urlsplit(value)
            if parsed.scheme != "https" or not parsed.netloc or parsed.path not in ("", "/") or parsed.query or parsed.fragment:
                raise _NexoraImproperlyConfigured(name + " doit contenir uniquement des origines HTTPS, sans chemin.")

    CORS_ALLOW_ALL_ORIGINS = False
    CORS_ALLOWED_ORIGINS = _nexora_csv("NEXORA_CORS_ALLOWED_ORIGINS")
    CSRF_TRUSTED_ORIGINS = _nexora_csv("NEXORA_CSRF_TRUSTED_ORIGINS")
    _nexora_validate_https_origins("NEXORA_CORS_ALLOWED_ORIGINS", CORS_ALLOWED_ORIGINS)
    _nexora_validate_https_origins("NEXORA_CSRF_TRUSTED_ORIGINS", CSRF_TRUSTED_ORIGINS)

    if not SECRET_KEY or len(str(SECRET_KEY)) < 50:
        raise _NexoraImproperlyConfigured("SECRET_KEY doit etre fournie par la configuration et compter au moins 50 caracteres.")

    MIDDLEWARE = list(MIDDLEWARE)
    _nexora_frame_middleware = "django.middleware.clickjacking.XFrameOptionsMiddleware"
    if _nexora_frame_middleware not in MIDDLEWARE:
        MIDDLEWARE.append(_nexora_frame_middleware)
    X_FRAME_OPTIONS = "DENY"
    SECURE_CONTENT_TYPE_NOSNIFF = True

    _nexora_https_mode = _nexora_os.environ.get("NEXORA_HTTPS_MODE", "").strip().lower()
    if _nexora_https_mode != "proxy":
        raise _NexoraImproperlyConfigured("Configurez d'abord un reverse proxy HTTPS, puis NEXORA_HTTPS_MODE=proxy.")
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    try:
        SECURE_HSTS_SECONDS = int(_nexora_os.environ.get("NEXORA_HSTS_SECONDS", "0"))
    except ValueError:
        raise _NexoraImproperlyConfigured("NEXORA_HSTS_SECONDS doit etre un entier.")
    if SECURE_HSTS_SECONDS < 0:
        raise _NexoraImproperlyConfigured("NEXORA_HSTS_SECONDS ne peut pas etre negatif.")
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False
    SECURE_REFERRER_POLICY = "same-origin"

    _nexora_jwt = dict(SIMPLE_JWT or {})
    _nexora_jwt["ACCESS_TOKEN_LIFETIME"] = _nexora_timedelta(minutes=30)
    _nexora_jwt["REFRESH_TOKEN_LIFETIME"] = _nexora_timedelta(hours=8)
    _nexora_jwt["ROTATE_REFRESH_TOKENS"] = True
    SIMPLE_JWT = _nexora_jwt

    _nexora_log_level = _nexora_os.environ.get("NEXORA_LOG_LEVEL", "INFO").upper()
    if _nexora_log_level not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
        raise _NexoraImproperlyConfigured("NEXORA_LOG_LEVEL n'est pas un niveau de journalisation reconnu.")
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "handlers": {"console": {"class": "logging.StreamHandler"}},
        "root": {"handlers": ["console"], "level": _nexora_log_level},
    }
'''


def assignments(tree):
    result = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    result.setdefault(target.id, []).append(node.value)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.value is not None:
            result.setdefault(node.target.id, []).append(node.value)
    return result


def references_environment(node):
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and child.id.lower() in ("env", "environ", "getenv"):
            return True
        if isinstance(child, ast.Attribute) and child.attr.lower() in ("environ", "getenv"):
            return True
    return False


def require_current_source(path):
    text = path.read_text(encoding="utf-8-sig")
    if MARKER in text:
        raise RuntimeError("Le profil existe deja; aucune modification n'a ete faite.")
    tree = ast.parse(text, filename="config/settings.py")
    found = assignments(tree)

    if len(found.get("DEBUG", [])) != 1 or not references_environment(found["DEBUG"][0]):
        raise RuntimeError("Precondition DEBUG non conforme a l'inspection; aucune modification n'a ete faite.")
    if len(found.get("SECRET_KEY", [])) != 1 or not references_environment(found["SECRET_KEY"][0]):
        raise RuntimeError("Precondition SECRET_KEY non conforme; aucune modification n'a ete faite.")
    allowed = found.get("ALLOWED_HOSTS", [])
    if len(allowed) != 1:
        raise RuntimeError("Precondition ALLOWED_HOSTS non conforme; aucune modification n'a ete faite.")
    try:
        allowed_value = ast.literal_eval(allowed[0])
    except (ValueError, TypeError, SyntaxError):
        raise RuntimeError("ALLOWED_HOSTS n'est pas une liste litterale; aucune modification n'a ete faite.")
    if not isinstance(allowed_value, (list, tuple)) or "*" not in allowed_value:
        raise RuntimeError("ALLOWED_HOSTS ne correspond pas au constat wildcard; aucune modification n'a ete faite.")
    cors = found.get("CORS_ALLOW_ALL_ORIGINS", [])
    if len(cors) != 1 or ast.literal_eval(cors[0]) is not True:
        raise RuntimeError("Precondition CORS_ALLOW_ALL_ORIGINS=True non conforme; aucune modification n'a ete faite.")
    if found.get("CORS_ALLOWED_ORIGINS") or found.get("CSRF_TRUSTED_ORIGINS"):
        raise RuntimeError("Des origines sont deja configurees dans le fichier; aucune modification n'a ete faite.")
    middleware = found.get("MIDDLEWARE", [])
    if len(middleware) != 1:
        raise RuntimeError("Precondition MIDDLEWARE non conforme; aucune modification n'a ete faite.")
    try:
        middleware_value = ast.literal_eval(middleware[0])
    except (ValueError, TypeError, SyntaxError):
        raise RuntimeError("MIDDLEWARE n'est pas une liste litterale; aucune modification n'a ete faite.")
    if not isinstance(middleware_value, (list, tuple)) or not any(
        str(item).endswith("SecurityMiddleware") for item in middleware_value
    ):
        raise RuntimeError("SecurityMiddleware introuvable; aucune modification n'a ete faite.")
    if any(str(item).endswith("XFrameOptionsMiddleware") for item in middleware_value):
        raise RuntimeError("XFrameOptionsMiddleware existe deja; aucune modification n'a ete faite.")
    if len(found.get("SIMPLE_JWT", [])) != 1:
        raise RuntimeError("Precondition SIMPLE_JWT non conforme; aucune modification n'a ete faite.")
    return text


def main():
    root = Path(__file__).resolve().parent
    manage = root / "manage.py"
    target = root / "config" / "settings.py"
    if os.name == "nt" and root.drive.upper() != "D:":
        raise RuntimeError("Placez les fichiers dans D:\\NEXORA, a cote de manage.py.")
    if not manage.is_file() or not target.is_file():
        raise RuntimeError("manage.py ou config/settings.py introuvable dans le dossier courant.")

    original_bytes = target.read_bytes()
    original_text = require_current_source(target)
    print("CIBLE=config/settings.py")
    print("SOURCE_VALIDEE=YES")
    print("MODE_LOCAL=inchangé; le profil reste inactif sans NEXORA_ENVIRONMENT=production")
    print("PRODUCTION=refuse de demarrer sans hote exact et reverse proxy HTTPS explicites")
    print("BACKUP=sera cree a cote du fichier avant toute modification")
    answer = input("Ajouter le profil dormant apres validation des preconditions ? Tapez OUI : ").strip().upper()
    if answer != "OUI":
        print("ANNULE=aucun fichier modifie")
        return 0

    if target.read_bytes() != original_bytes:
        raise RuntimeError("Le fichier a change depuis le controle; relancez le script sans modification concurrente.")

    newline = "\r\n" if "\r\n" in original_text else "\n"
    profile = PROFILE.replace("\n", newline)
    separator = "" if original_text.endswith(("\n", "\r")) else newline
    updated_text = original_text + separator + newline + profile
    ast.parse(updated_text, filename="config/settings.py")

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    backup = target.with_name(target.name + ".pre-nexora-profile-" + stamp + ".bak")
    temporary = target.with_name(target.name + ".nexora-profile-" + stamp + ".tmp")
    with backup.open("xb") as stream:
        stream.write(original_bytes)
    try:
        encoding = "utf-8-sig" if original_bytes.startswith(b"\xef\xbb\xbf") else "utf-8"
        temporary.write_text(updated_text, encoding=encoding, newline="")
        os.replace(str(temporary), str(target))
    except Exception:
        try:
            temporary.unlink()
        except OSError:
            pass
        try:
            if target.read_bytes() != original_bytes:
                target.write_bytes(original_bytes)
        except OSError:
            pass
        raise

    print("PATCH_OK=profil de production ajoute, inactif en mode local")
    print("BACKUP_RELATIVE=config/" + backup.name)
    print("AUCUNE_MIGRATION=YES")
    print("PROCHAINE_ETAPE=arreter puis relancer start-local-postgresql.bat pour verifier le mode local")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("ECHEC=" + str(exc))
        sys.exit(1)
