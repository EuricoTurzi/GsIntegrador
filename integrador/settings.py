"""
Django settings for integrador project.
"""

from pathlib import Path
import environ
import os
from datetime import timedelta

# Inicializar environ
env = environ.Env(
    DEBUG=(bool, False)
)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Ler arquivo .env
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY', default='django-insecure-dev-key-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG', default=True)

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])


# Application definition

INSTALLED_APPS = [
    # Django apps
    'daphne',  # Deve vir ANTES de django.contrib.staticfiles
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps
    'channels',  # Django Channels para WebSocket
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    'crispy_forms',
    'crispy_bootstrap5',
    'django_celery_beat',
    'django_celery_results',
    
    # Local apps
    'apps.authentication',
    'apps.drivers',
    'apps.vehicles',
    'apps.devices',
    'apps.integrations',
    'apps.routes',
    'apps.monitoring',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'integrador.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'integrador.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': env('DB_ENGINE', default='django.db.backends.sqlite3'),
        'NAME': env('DB_NAME', default=str(BASE_DIR / 'db.sqlite3')),
        'USER': env('DB_USER', default=''),
        'PASSWORD': env('DB_PASSWORD', default=''),
        'HOST': env('DB_HOST', default=''),
        'PORT': env('DB_PORT', default=''),
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'pt-br'

TIME_ZONE = env('TIME_ZONE', default='America/Sao_Paulo')

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Custom User Model
AUTH_USER_MODEL = 'authentication.User'


# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100,
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}


# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=12),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
}


# CORS Settings
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[
    'http://localhost:3000',
    'http://127.0.0.1:3000',
])

CORS_ALLOW_CREDENTIALS = True


# Celery Configuration
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes


# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"


# Suntech API Configuration
SUNTECH_API_BASE_URL = env('SUNTECH_API_BASE_URL', default='https://ap3.stc.srv.br/integration/prod/ws/')
SUNTECH_API_KEY = env('SUNTECH_API_KEY', default='')
SUNTECH_API_USER = env('SUNTECH_API_USER', default='')
SUNTECH_API_PASS = env('SUNTECH_API_PASS', default='')

# OpenRouteService API Configuration (for routing and geocoding)
OPENROUTESERVICE_API_KEY = env('OPENROUTESERVICE_API_KEY', default='')

# Device Update Threshold (in minutes)
DEVICE_UPDATE_THRESHOLD_MINUTES = 30


# Debug Toolbar (apenas em desenvolvimento)
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    INTERNAL_IPS = ['127.0.0.1']

# Authentication settings
LOGIN_URL = '/auth/login/'
LOGIN_REDIRECT_URL = '/'

# ===================================================================
# CHANNELS & WEBSOCKET CONFIGURATION
# ===================================================================

# ASGI Application
ASGI_APPLICATION = 'integrador.asgi.application'

# Channel Layers - usando Redis como backend
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [(env('REDIS_HOST', default='redis'), env.int('REDIS_PORT', default=6379))],
            "capacity": 1500,  # Número máximo de mensagens no canal
            "expiry": 10,  # Tempo de expiração das mensagens (segundos)
        },
    },
}

# ===================================================================
# CELERY CONFIGURATION
# ===================================================================

# Celery Configuration usando Redis como broker
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://redis:6379/0')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://redis:6379/0')
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True

# Celery Beat Schedule - tarefas periódicas
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'sync-devices-every-minute': {
        'task': 'devices.sync_all_devices',  # Nome registrado no @shared_task
        'schedule': crontab(minute='*'),  # A cada 1 minuto (monitoramento em tempo real)
    },
    'broadcast-fleet-positions-every-30-seconds': {
        'task': 'monitoring.broadcast_fleet_positions',  # Nome registrado no @shared_task
        'schedule': 30.0,  # A cada 30 segundos
    },
}

# ===================================================================
# REDIS CACHE CONFIGURATION
# ===================================================================

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': f"redis://{env('REDIS_HOST', default='redis')}:{env.int('REDIS_PORT', default=6379)}/1",
        'OPTIONS': {
            'db': 1,
            # parser_class removido - não existe mais no redis-py 5.x
            'pool_class': 'redis.BlockingConnectionPool',
        }
    }
}
LOGOUT_REDIRECT_URL = '/auth/login/'
