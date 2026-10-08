import os
from pathlib import Path
from datetime import timedelta
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def _nexora_charger_env_local():
    """Charge BASE_DIR/.env s'il existe (sans dependance externe).

    Permet de regler l'application par un simple fichier texte a cote de
    manage.py, sans script ni variable d'environnement systeme. Les variables
    deja definies dans l'environnement gardent la priorite.
    """
    fichier = BASE_DIR / '.env'
    if not fichier.exists():
        return
    try:
        for ligne in fichier.read_text(encoding='utf-8').splitlines():
            ligne = ligne.strip()
            if not ligne or ligne.startswith('#') or '=' not in ligne:
                continue
            cle, valeur = ligne.split('=', 1)
            cle = cle.strip()
            valeur = valeur.strip().strip('"').strip("'")
            if cle and cle not in os.environ:
                os.environ[cle] = valeur
    except OSError:
        pass


_nexora_charger_env_local()

CLE_SECRETE_PAR_DEFAUT = 'nexora-secret-key-change-in-production-random-hash-919293'

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', CLE_SECRETE_PAR_DEFAUT)

DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

if DEBUG:
    # Poste de caisse / developpement : rien ne change, l'application reste
    # joignable par son nom ou son adresse IP locales.
    ALLOWED_HOSTS = ['*']
else:
    # Mode production : seuls les noms declares sont acceptes.
    ALLOWED_HOSTS = [
        hote.strip() for hote in os.environ.get(
            'NEXORA_ALLOWED_HOSTS', 'localhost,127.0.0.1,[::1]'
        ).split(',') if hote.strip()
    ]

    if SECRET_KEY == CLE_SECRETE_PAR_DEFAUT:
        raise ImproperlyConfigured(
            "DJANGO_SECRET_KEY doit etre defini lorsque DJANGO_DEBUG=False "
            "(la cle livree dans le code source est publique)."
        )

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'django_filters',
    'corsheaders',
    'drf_spectacular',

    # NEXORA Apps
    'apps.common',
    'apps.companies',
    'apps.accounts',
    'apps.catalog',
    'apps.partners',
    'apps.inventory',
    'apps.pos',
    'apps.sales',
    'apps.purchases',
    'apps.reports',
    'apps.notifications',
    'apps.audit',
    'apps.ai_assistant',
]

MIDDLEWARE = [
    # Masque les pages de diagnostic Django (404/500 bavardes) pour tout appel
    # qui ne vient pas du poste de caisse. Sur le poste, rien ne change.
    'apps.common.middleware.DebugLocalSeulementMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # Garde unique du reseau : tout appel anonyme a /api/v1/ venu d'une autre
    # machine est refuse (placee apres AuthenticationMiddleware pour connaitre
    # l'utilisateur eventuellement deja connecte par session).
    'apps.common.middleware.GardeReseauMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'apps.common.middleware.FrameOptionsMiddleware',
    'apps.audit.middleware.SecurityAuditLoggingMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
# Defaults to SQLite for immediate portable setup, easily configurable to PostgreSQL via DATABASE_URL
DB_ENGINE = os.environ.get('DB_ENGINE', 'sqlite')
if DB_ENGINE == 'postgresql':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', 'nexora_db'),
            'USER': os.environ.get('DB_USER', 'nexora'),
            'PASSWORD': os.environ.get('DB_PASSWORD', 'nexora_secret'),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_USER_MODEL = 'accounts.User'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8},
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'apps.common.authentication.OptionalJWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
    ),
    'DEFAULT_PAGINATION_CLASS': 'apps.common.pagination.StandardResultsSetPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_RATES': {
        # Limite les tentatives de connexion (10 par minute et par adresse).
        'connexion': os.environ.get('NEXORA_THROTTLE_CONNEXION', '10/min'),
    },
    'EXCEPTION_HANDLER': 'apps.common.exceptions.custom_exception_handler',
}

# SimpleJWT settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': False,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# drf-spectacular OpenAPI Settings
SPECTACULAR_SETTINGS = {
    'TITLE': 'NEXORA API',
    'DESCRIPTION': 'Documentation OpenAPI 3.0 de l\'API d\'Entreprise NEXORA : Vente, Gestion de Stock, Achats, Caisses, Multi-Tenant & Anticipation.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
}

# CORS configuration
# Avant, TOUTE origine etait acceptee : une page web ouverte dans le meme
# navigateur pouvait lire l'API (ventes, clients, produits) via 127.0.0.1.
# Desormais, seules les origines locales et de reseau prive sont acceptees,
# et NEXORA_CORS_ORIGINES permet d'ajouter une origine precise si besoin.
CORS_ALLOW_ALL_ORIGINS = os.environ.get('NEXORA_CORS_TOUT_AUTORISE', 'False') == 'True'
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    origine.strip() for origine in os.environ.get('NEXORA_CORS_ORIGINES', '').split(',')
    if origine.strip()
]
CORS_ALLOWED_ORIGIN_REGEXES = [
    r'^http://localhost(:\d+)?$',
    r'^http://127\.0\.0\.1(:\d+)?$',
    r'^http://\[::1\](:\d+)?$',
    r'^http://10\.\d{1,3}\.\d{1,3}\.\d{1,3}(:\d+)?$',
    r'^http://192\.168\.\d{1,3}\.\d{1,3}(:\d+)?$',
    r'^http://172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}(:\d+)?$',
]
CORS_EXPOSE_HEADERS = ['Content-Disposition', 'Content-Length', 'Content-Type']

# Charge utile des PDF : les liens directs ouvrent le document dans un onglet
# ou un apercu integre sans jeton. On conserve donc l'exemption pour les PDF
# (voir FrameOptionsMiddleware) tout en refusant l'inclusion des pages HTML.
X_FRAME_OPTIONS = os.environ.get('NEXORA_X_FRAME_OPTIONS', 'SAMEORIGIN')

# Mode caisse locale : appels sans jeton acceptes depuis le poste uniquement.
NEXORA_CAISSE_LOCALE = os.environ.get('NEXORA_CAISSE_LOCALE', 'True')

# En-tetes de durcissement sans effet de bord (ne cassent aucun usage local).
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'

