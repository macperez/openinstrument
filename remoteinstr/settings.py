"""
Django settings for remoteinstr project.

Generated by 'django-admin startproject' using Django 1.8.4.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '&ko-1(+a5rf+-f5bo*lbj%&av-^nkvj_q2a)8v#cu8-r-s&w1g'

# SECURITY WARNING: don't run with debug turned on in production!
# remoteinstr
DEBUG = True

# ALLOWED_HOSTS = ['localhost', '127.0.0.1']
ALLOWED_HOSTS = []

# remoteinstr
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'remoteinstrapp.permission.SimpleAuthentication',

    )
}



# remoteinstr
from datetime import timedelta  # Beat Celery config: (configured by Manu)
# remoteinstr
DATE_FORMAT_ISO_8601 = '%Y-%m-%d %H:%M:%S.%3d'
DATE_FORMAT_EXTERNAL_WEB_SERVICE = '%Y-%m-%dT%H:%M:%S'

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'remoteinstrapp',
    'kombu.transport.django',  # useful for celery tasks
    'daemonsceleryapp',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
)

ROOT_URLCONF = 'remoteinstr.urls'

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

WSGI_APPLICATION = 'remoteinstr.wsgi.application'


# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Madrid'

USE_I18N = True

USE_L10N = True

# remoteinstr
USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'


# CORS
# remoteinstr
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_HEADERS = (
    'x-requested-with',
    'content-type',
    'accept',
    'origin',
    'authorization',
    'x-csrftoken',
    'api-key',
)
# remoteinstr
CORS_ALLOW_METHODS = (
    'GET',
    'PUT',
    'POST',
    'DELETE',
    'OPTIONS',
    'PATCH',
)

# remoteinstr logger (configured by manu)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': {
        'verbose': {
            'format': "[%(asctime)s] %(levelname)s [%(name)s:%(funcName)s:%(lineno)s] %(message)s",
            'datefmt': DATE_FORMAT_EXTERNAL_WEB_SERVICE
        },
        'simple': {
            'format': '%(levelname)s | %(funcName)s | %(message)s'
        },
    },

    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'remoteinstr.log',
            'formatter': 'verbose'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
    },
    'loggers': {
        'remoteinstrapp': {
            # 'handlers': ['console','file'],
            'level': 'DEBUG',
        },
        'daemonsceleryapp': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
        },

    }
}

# ********** REMOTEINSTR SETTING **************************

# Broker Celery. Onlyh change if you have installed Reddit or RabbitQM...
BROKER_URL = 'django://'

# APIKEY elemmental authentication, all the users must include in their header requests.
API_KEY = 'ebd_web_service'

# Set to true if there was something wrong with the installation of a backend
DEACTIVATE_CHECK_BACKENDS = False

# Basic Authentication vs LifeWatch server: FOR send_task daemon
SEND_DATA_ENDPOINT_URL = 'http://lifewatch.viavansi.com/lifewatch-service-rest/instrumentContent/createlist'
SEND_DATA_ENDPOINT_USER = 'lifewatch_user'
SEND_DATA_ENDPOINT_PASSWORD = 'lifewatch_pass'

# The number of threads (tasks)  opened per worker.
CELERYD_CONCURRENCY = 1

# Task schedule
CELERYBEAT_SCHEDULE = {

    # Recogida de datos de los instrumentos, los resultados se almacenan en una tabla temporal
    'collect-data': {
        'task': 'daemonsceleryapp.tasks.collect_data',
        'schedule': timedelta(seconds=10),  # CONFIGURABLE --> periodo en segundos de ejecucin de la tarea
        'options': {
            'expires': 20
        },
    },

    # Envio de datos de los instrumentos a una URL externa.
    'send-data': {
        'task': 'daemonsceleryapp.tasks.send_data',
        'schedule': timedelta(seconds=1000),  # CONFIGURABLE --> periodo en segundos de ejecucin de la tarea
        'args': (SEND_DATA_ENDPOINT_URL, SEND_DATA_ENDPOINT_USER, SEND_DATA_ENDPOINT_PASSWORD, 15),  # CONFIGURABLE ->-
        #  URL remota, Tamao del bloque de registros
        'options': {
            'expires': 20
        },

    },

    # Limpieza de datos temporales.
    'clean-data': {
        'task': 'daemonsceleryapp.tasks.clean_data',
        'schedule': timedelta(seconds=4000),  # CONFIGURABLE --> URL remota, TIEMPO DE EJECUCIN DE LA TAREA EN SEGUNDOS
        'args': (1140,)  # CONFIGURABLE --> tiempo de antiguedad de los datos que van a ser limpiado EN MINUTOS

    },

}

# Base de datos
# remoteinstr
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'remoteinstr.db'),
    }
    # ,
    # 'defaultl': {
    #    'ENGINE': 'django.db.backends.mysql',
    #    'NAME': 'ebd',
    #    'USER': 'ebduser',
    #    'PASSWORD': 'ebdpass',
    #    'HOST': 'localhost',
    #    'PORT': '',
    # }
}
