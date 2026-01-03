"""
Django settings for monprojet project.
Configuration pour le serveur principal
"""

from pathlib import Path
import os
import pymysql

# Initialisation pymysql pour MariaDB
pymysql.install_as_MySQLdb()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings
SECRET_KEY = 'django-insecure-=%@qe%eu)2sm61e6h2nsh_di#a7mfqkdac09i-2kg*eavf*m7y'
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']


DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50 MB

# Pour les fichiers très volumineux
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000
# ============================================
# CONFIGURATION DES SERVICES EXTERNES
# ============================================

# URLs des autres services
AUTH_SERVICE_URL = 'http://127.0.0.1:8001' 
AUTH_API_URL = f"{AUTH_SERVICE_URL}/api/auth/"      # Serveur d'authentification
COURSES_SERVICE_URL = 'http://127.0.0.1:8002'   # Serveur de cours

# Secret JWT partagé
JWT_SECRET_KEY = 'votre-secret-jwt-partage'

# ============================================
# CONFIGURATION DJANGO
# ============================================


INSTALLED_APPS = [
    # Django core
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'pages',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
]

ROOT_URLCONF = 'monprojet.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates",  # Cherche dans main_server/templates/
            BASE_DIR / "pages" / "templates",
            ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                #'pages.context_processors.auth_context',
            ],
        },
    }
]

WSGI_APPLICATION = 'monprojet.wsgi.application'

# ============================================
# BASE DE DONNÉES
# ============================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'learnhub',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        }
    }
}

# ============================================
# AUTHENTIFICATION
# ============================================

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ============================================
# INTERNATIONALISATION
# ============================================

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_TZ = True

# ============================================
# FICHIERS STATIQUES
# ============================================

STATIC_URL = 'static/'
STATICFILES_DIRS = [] 

MEDIA_URL = '/media/'  # IMPORTANT: doit finir par /
MEDIA_ROOT = os.path.join(BASE_DIR, 'media') 
# ============================================
# DEFAUT AUTO FIELD
# ============================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================
# URLs DE REDIRECTION
# ============================================

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'