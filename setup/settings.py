from pathlib import Path

import os

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-chave-padrao-desenvolvimento')

DEBUG = os.getenv('DEBUG', 'False') == 'True'

VAPID_PUBLIC_KEY = os.getenv('VAPID_PUBLIC_KEY', 'BFLk6_JdSQnw2tF8upjINQuU831-MEP92iLNSccazaBh5CKAW3qSUkwJSHM8N38cfJO3rNvAGc5CfetVVgWs5NM')

VAPID_PRIVATE_KEY = os.getenv('VAPID_PRIVATE_KEY', 'vsIus-mzPP8jOr-wU7hLmRI3WDWSe7XoTc-mqeqZtLw')

VAPID_ADMIN_EMAIL = os.getenv('VAPID_ADMIN_EMAIL', 'mailto:discipuloleonardo@gmail.com')

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,*').split(',')

_csrf_origins_env = os.getenv('CSRF_TRUSTED_ORIGINS', '')

CSRF_TRUSTED_ORIGINS = [

    'http://localhost:8000',

    'http://127.0.0.1:8000',

    'http://192.168.1.49:8000',

] + [o.strip() for o in _csrf_origins_env.split(',') if o.strip()]

CSRF_COOKIE_SAMESITE = 'Lax'

SESSION_COOKIE_SAMESITE = 'Lax'

CSRF_COOKIE_HTTPONLY = False

SECURE_BROWSER_XSS_FILTER = True

SECURE_CONTENT_TYPE_NOSNIFF = True

X_FRAME_OPTIONS = 'SAMEORIGIN'

if not DEBUG:

    CSRF_COOKIE_SECURE = True

    SESSION_COOKIE_SECURE = True

    SECURE_SSL_REDIRECT = True

    SECURE_HSTS_SECONDS = 31536000         

    SECURE_HSTS_INCLUDE_SUBDOMAINS = True

    SECURE_HSTS_PRELOAD = True

INSTALLED_APPS = [

    'unfold',                                         

    'unfold.contrib.filters',                     

    'unfold.contrib.forms',                          

    'unfold.contrib.import_export',                                

    'django.contrib.admin',

    'django.contrib.auth',

    'django.contrib.sites',

    'django.contrib.contenttypes',

    'django.contrib.sessions',

    'django.contrib.messages',

    'django.contrib.staticfiles',

    'import_export',                    

    'allauth',

    'allauth.account',

    'allauth.socialaccount',

    'allauth.socialaccount.providers.google',

    'portaria',           

]

MIDDLEWARE = [

    'django.middleware.security.SecurityMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',

    'django.middleware.common.CommonMiddleware',

    'django.middleware.csrf.CsrfViewMiddleware',

    'django.contrib.auth.middleware.AuthenticationMiddleware',

    'django.contrib.messages.middleware.MessageMiddleware',

    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    'allauth.account.middleware.AccountMiddleware',

]

ROOT_URLCONF = 'setup.urls'

TEMPLATES = [

    {

        'BACKEND': 'django.template.backends.django.DjangoTemplates',

        'DIRS': [os.path.join(BASE_DIR, 'portaria', 'templates')],

        'APP_DIRS': True,

        'OPTIONS': {

            'context_processors': [

                'django.template.context_processors.request',

                'django.contrib.auth.context_processors.auth',

                'django.contrib.messages.context_processors.messages',

                'portaria.context_processors.notificacoes',

                'portaria.context_processors.condominio_info',

            ],

        },

    },

]

WSGI_APPLICATION = 'setup.wsgi.application'

DATABASES = {

    'default': {

        'ENGINE': 'django.db.backends.sqlite3',

        'NAME': BASE_DIR / 'db.sqlite3',

    }

}

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

LANGUAGE_CODE = 'pt-br'

TIME_ZONE = 'America/Sao_Paulo'

USE_I18N = True

USE_TZ = True

STATIC_URL = 'static/'

STATIC_ROOT = os.path.join(BASE_DIR, 'staticcollect')

STATICFILES_DIRS = [

    os.path.join(BASE_DIR, 'static'),

]

MEDIA_URL = '/media/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800

FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'portaria.CustomUser'

LOGIN_REDIRECT_URL = 'home'

LOGIN_URL = 'login'

LOGOUT_REDIRECT_URL = 'login'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = 'smtp.gmail.com'

EMAIL_PORT = 465

EMAIL_USE_TLS = False

EMAIL_USE_SSL = True

EMAIL_TIMEOUT = 10

EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')

EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')

DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', f'Gestão Condominial <{EMAIL_HOST_USER}>')

from django.urls import reverse_lazy

UNFOLD = {

    "SITE_TITLE": "KS TECH - Gestão de Ativos",

    "SITE_HEADER": "KS TECH - Gestão de Ativos",

    "SITE_SUBHEADER": "Painel de Administração SaaS",

    "SITE_URL": "/admin/",

    "SITE_SYMBOL": "apartment",

    "SHOW_HISTORY": True,

    "SHOW_VIEW_ON_SITE": False,

    "SHOW_BACK_BUTTON": True,

    "BORDER_RADIUS": "8px",

    "DASHBOARD_CALLBACK": "portaria.dashboard.dashboard_callback",

    "COLORS": {

        "base": {

            "50": "250 250 252",

            "100": "241 245 249",

            "200": "226 232 240",

            "300": "203 213 225",

            "400": "148 163 184",

            "500": "100 116 139",

            "600": "71 85 105",

            "700": "51 65 85",

            "800": "30 41 59",

            "900": "15 23 42",

            "950": "2 6 23",

        },

        "primary": {

            "50": "239 246 255",

            "100": "219 234 254",

            "200": "191 219 254",

            "300": "147 197 253",

            "400": "96 165 250",

            "500": "59 130 246",

            "600": "37 99 235",

            "700": "29 78 216",

            "800": "30 64 175",

            "900": "30 58 138",

            "950": "23 37 84",

        },

    },

    "SIDEBAR": {

        "show_search": True,

        "show_all_applications": False,

        "navigation": [

            {

                "title": "Painel",

                "separator": True,

                "collapsible": False,

                "items": [

                    {

                        "title": "Dashboard",

                        "icon": "dashboard",

                        "link": reverse_lazy("admin:index"),

                    },

                ],

            },

            {

                "title": "Gestão de Locatários",

                "separator": True,

                "collapsible": False,

                "items": [

                    {

                        "title": "Condomínios",

                        "icon": "apartment",

                        "link": reverse_lazy("admin:portaria_condominio_changelist"),

                    },

                    {

                        "title": "Síndicos",

                        "icon": "admin_panel_settings",

                        "link": reverse_lazy("admin:portaria_sindico_changelist"),

                    },

                    {

                        "title": "Porteiros",

                        "icon": "badge",

                        "link": reverse_lazy("admin:portaria_porteiro_changelist"),

                    },

                    {

                        "title": "Moradores",

                        "icon": "people",

                        "link": reverse_lazy("admin:portaria_morador_changelist"),

                    },

                ],

            },

            {

                "title": "Acesso",

                "separator": True,

                "collapsible": True,

                "items": [

                    {

                        "title": "Usuários",

                        "icon": "person",

                        "link": reverse_lazy("admin:portaria_customuser_changelist"),

                    },

                    {

                        "title": "Grupos",

                        "icon": "group",

                        "link": reverse_lazy("admin:auth_group_changelist"),

                    },

                ],

            },

            {

                "title": "Autenticação e Domínio",

                "separator": True,

                "collapsible": True,

                "items": [

                    {

                        "title": "Domínios do Sistema",

                        "icon": "language",

                        "link": reverse_lazy("admin:sites_site_changelist"),

                    },

                    {

                        "title": "Login Social (Google)",

                        "icon": "key",

                        "link": reverse_lazy("admin:socialaccount_socialapp_changelist"),

                    },

                ],

            },

        ],

    },

}

SITE_ID = 1

AUTHENTICATION_BACKENDS = [

    'django.contrib.auth.backends.ModelBackend',

    'allauth.account.auth_backends.AuthenticationBackend',

]

SOCIALACCOUNT_PROVIDERS = {

    'google': {

        'SCOPE': [

            'profile',

            'email',

        ],

        'AUTH_PARAMS': {

            'access_type': 'online',

        },

        'OAUTH_PKCE_ENABLED': True,

    }

}

SOCIALACCOUNT_ADAPTER = 'portaria.adapters.MySocialAccountAdapter'

SOCIALACCOUNT_LOGIN_ON_GET = True

LOGIN_REDIRECT_URL = '/login/popup-close/'

ACCOUNT_LOGIN_METHODS = {'email'}

ACCOUNT_SIGNUP_FIELDS = ['email*']

ACCOUNT_UNIQUE_EMAIL = True

SOCIALACCOUNT_AUTO_SIGNUP = True

