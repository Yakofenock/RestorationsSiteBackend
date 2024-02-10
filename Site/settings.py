from pathlib import Path
from configparser import ConfigParser

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG = ConfigParser()
CONFIG.read(BASE_DIR / 'config.cfg')

LOGS_DIR = BASE_DIR / 'logs'
MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'
INFO_LOG = LOGS_DIR / 'info.log'
ERR_LOG = LOGS_DIR / 'errors.log'
INFO_LOG.touch(), ERR_LOG.touch()

SECRET_KEY = CONFIG.get('Django', 'secret_key')
ALLOWED_HOSTS = ['127.0.0.1']
CSRF_TRUSTED_ORIGINS = ['http://localhost:3000', 'http://127.0.0.1:3000']
DEBUG = True

MONEY_SYMBOL = '₽'
ROUND = 4
DIGITS_RU_NAMES = {1_000_000_000: 'млрд.', 1_000_000: 'млн.', 1_000: 'тыс.'}

ROOT_URLCONF = 'Site.urls'
WSGI_APPLICATION = 'Site.wsgi.application'
STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'storages',
    'rest_framework',
    'drf_yasg',
    'Restorations',
    'Profiles'
]

# Async web service:
WEB_SERVICE_SEKRET_KEY = CONFIG.get('GO', 'key')

# Minio settings:
STATICFILES_STORAGE = 'Site.boto_fixer.JSFixedS3Boto3Storage'
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

AWS_S3_ENDPOINT_URL = str(CONFIG.get('Minio', 'url'))
AWS_ACCESS_KEY_ID       = CONFIG.get('Minio', 'key_id')
AWS_SECRET_ACCESS_KEY   = CONFIG.get('Minio', 'access_key')
AWS_STORAGE_BUCKET_NAME = CONFIG.get('Minio', 'bucket_name')
AWS_QUERYSTRING_AUTH = False
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None

# Redis settings:
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": CONFIG.get('Redis', 'url'),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME':     CONFIG.get('Postgres DB', 'name'),
        'USER':     CONFIG.get('Postgres DB', 'user'),
        'PASSWORD': CONFIG.get('Postgres DB', 'password'),
        'HOST':     CONFIG.get('Postgres DB', 'host'),
        'PORT':     CONFIG.get('Postgres DB', 'port')
    }
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'formatter': {
            'format': '{levelname} - {asctime} - {module} - {process:d} - {thread:d} - {message}',
            'style': '{',
        },
    },
    'handlers': {
        'info': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': INFO_LOG,
        },
        'errors': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': ERR_LOG,
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['info', 'errors', 'console'],
            'formatter': 'formatter',
            'level': 'INFO',
            'propagate': False
        },
    },
}

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

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',          },
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',         },
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',        },
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
