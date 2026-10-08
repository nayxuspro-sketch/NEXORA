# -*- coding: utf-8 -*-
"""Affiche des indicateurs Django non secrets et verifie la cible PostgreSQL.

Usage local par audit-securite-production.ps1. Toutes les requetes sont en lecture seule.
Ne jamais imprimer settings.SECRET_KEY, DATABASES['default']['PASSWORD'] ou les hote/origines exacts.
"""

import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

try:
    import django
    django.setup()
    from django.conf import settings
    from django.db import connection
except Exception as exc:  # Ne pas afficher un message qui pourrait contenir une valeur sensible.
    print("DJANGO_SETUP=FAIL")
    print("DJANGO_SETUP_ERROR_TYPE=" + type(exc).__name__)
    sys.exit(1)


def emit(name, value):
    print("{}={}".format(name, value))


def yes_no(value):
    return "YES" if bool(value) else "NO"


def count_setting(value):
    if value is None:
        return 0
    if isinstance(value, str):
        return 1 if value else 0
    try:
        return len(value)
    except TypeError:
        return 1


db = settings.DATABASES.get("default", {})
db_name = str(db.get("NAME", ""))
db_user = str(db.get("USER", ""))
db_host = str(db.get("HOST", ""))
emit("DJANGO_SETUP", "OK")
emit("DJANGO_VERSION", django.get_version())
emit("SETTINGS_MODULE", getattr(settings, "SETTINGS_MODULE", "unknown"))
emit("DATABASE_ENGINE", db.get("ENGINE", ""))
emit("DATABASE_NAME_MATCH_NEXORA_DB", yes_no(db_name == "nexora_db"))
emit("DATABASE_USER_MATCH_NEXORA", yes_no(db_user == "nexora"))
emit("DATABASE_HOST_LOCAL", yes_no(db_host in ("", "127.0.0.1", "localhost", "::1")))
emit("DATABASE_PORT_CONFIGURED", yes_no(bool(db.get("PORT", ""))))
emit("DATABASE_CONN_MAX_AGE", db.get("CONN_MAX_AGE", 0))
emit("DATABASE_ATOMIC_REQUESTS", yes_no(db.get("ATOMIC_REQUESTS", False)))
emit("DATABASE_PASSWORD", "REDACTED")
emit("SECRET_KEY", "REDACTED")

try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT current_user, current_database(), current_setting('server_version')")
        current_user, current_database, server_version = cursor.fetchone()
    emit("POSTGRESQL_CURRENT_USER_MATCH", yes_no(current_user == "nexora"))
    emit("POSTGRESQL_CURRENT_DATABASE_MATCH", yes_no(current_database == "nexora_db"))
    emit("POSTGRESQL_SERVER_VERSION", server_version)
    if connection.vendor != "postgresql" or current_user != "nexora" or current_database != "nexora_db":
        emit("POSTGRESQL_TARGET", "FAIL")
        sys.exit(2)
    emit("POSTGRESQL_TARGET", "OK")
except Exception as exc:  # Ne pas afficher DSN ou details du pilote.
    emit("POSTGRESQL_TARGET", "FAIL")
    emit("DATABASE_ERROR_TYPE", type(exc).__name__)
    sys.exit(2)

allowed_hosts = getattr(settings, "ALLOWED_HOSTS", None) or []
if isinstance(allowed_hosts, str):
    allowed_hosts = [allowed_hosts]
emit("DEBUG", yes_no(getattr(settings, "DEBUG", True)))
emit("ALLOWED_HOSTS_COUNT", count_setting(allowed_hosts))
emit("ALLOWED_HOSTS_EMPTY", yes_no(not allowed_hosts))
emit("ALLOWED_HOSTS_HAS_WILDCARD", yes_no("*" in allowed_hosts))

cors_all = getattr(
    settings,
    "CORS_ALLOW_ALL_ORIGINS",
    getattr(settings, "CORS_ORIGIN_ALLOW_ALL", False),
)
cors_origins = getattr(
    settings,
    "CORS_ALLOWED_ORIGINS",
    getattr(settings, "CORS_ORIGIN_WHITELIST", None),
)
emit("CORS_ALLOW_ALL_ORIGINS", yes_no(cors_all))
emit("CORS_ALLOWED_ORIGINS_COUNT", count_setting(cors_origins))
emit("CSRF_TRUSTED_ORIGINS_COUNT", count_setting(getattr(settings, "CSRF_TRUSTED_ORIGINS", None)))

secret_key = str(getattr(settings, "SECRET_KEY", "") or "")
emit("SECRET_KEY_PRESENT", yes_no(bool(secret_key)))
emit("SECRET_KEY_LENGTH_AT_LEAST_50", yes_no(len(secret_key) >= 50))

for name in (
    "SECURE_SSL_REDIRECT",
    "SESSION_COOKIE_SECURE",
    "CSRF_COOKIE_SECURE",
    "SECURE_CONTENT_TYPE_NOSNIFF",
    "SECURE_HSTS_INCLUDE_SUBDOMAINS",
    "SECURE_HSTS_PRELOAD",
):
    emit(name, yes_no(getattr(settings, name, False)))
emit("SECURE_HSTS_SECONDS", getattr(settings, "SECURE_HSTS_SECONDS", 0) or 0)
emit("SECURE_PROXY_SSL_HEADER_CONFIGURED", yes_no(bool(getattr(settings, "SECURE_PROXY_SSL_HEADER", None))))

middleware = list(getattr(settings, "MIDDLEWARE", []) or [])
installed_apps = list(getattr(settings, "INSTALLED_APPS", []) or [])
logging_config = getattr(settings, "LOGGING", {}) or {}
logging_handlers = logging_config.get("handlers", {}) or {}
emit("WHITENOISE_CONFIGURED", yes_no(any("whitenoise" in str(item).lower() for item in middleware + installed_apps)))
emit("STATIC_ROOT_CONFIGURED", yes_no(bool(getattr(settings, "STATIC_ROOT", ""))))
emit("MEDIA_ROOT_CONFIGURED", yes_no(bool(getattr(settings, "MEDIA_ROOT", ""))))
emit("LOGGING_HANDLERS_COUNT", count_setting(logging_handlers))
emit("LANGUAGE_CODE", getattr(settings, "LANGUAGE_CODE", "unknown"))
emit("USE_TZ", yes_no(getattr(settings, "USE_TZ", False)))

blacklist_app = "rest_framework_simplejwt.token_blacklist" in installed_apps
emit("JWT_BLACKLIST_APP_INSTALLED", yes_no(blacklist_app))
try:
    from rest_framework_simplejwt.settings import api_settings as jwt_settings

    emit("JWT_AVAILABLE", "YES")
    emit("JWT_ROTATE_REFRESH_TOKENS", yes_no(jwt_settings.ROTATE_REFRESH_TOKENS))
    emit("JWT_ACCESS_TOKEN_MINUTES", int(jwt_settings.ACCESS_TOKEN_LIFETIME.total_seconds() // 60))
    emit("JWT_REFRESH_TOKEN_HOURS", int(jwt_settings.REFRESH_TOKEN_LIFETIME.total_seconds() // 3600))
except Exception:
    emit("JWT_AVAILABLE", "NO_OR_UNREADABLE")

print("NOTE=Hostnames, CORS origins, passwords and SECRET_KEY values are intentionally omitted.")
