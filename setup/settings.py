from pathlib import Path
import os
from dotenv import load_dotenv


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-chave-padrao-desenvolvimento')

DEBUG = os.getenv('DEBUG', 'False') == 'True'

# Hosts permitidos (separados por vírgula no .env)
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,*').split(',')

# Origens confiáveis para CSRF (necessário para acesso via IP na rede local)
# Configurável via .env: CSRF_TRUSTED_ORIGINS=http://192.168.1.49:8000,http://192.168.1.50:8000
_csrf_origins_env = os.getenv('CSRF_TRUSTED_ORIGINS', '')
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'http://192.168.1.49:8000',
] + [o.strip() for o in _csrf_origins_env.split(',') if o.strip()]

# Cookies compatíveis com iOS WebKit (Chrome no iPhone usa WebKit)
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_HTTPONLY = False

# ==============================================================================
# CONFIGURAÇÕES DE SEGURANÇA
# ==============================================================================

# Proteção contra XSS
SECURE_BROWSER_XSS_FILTER = True

# Evita que o navegador interprete arquivos incorretamente
SECURE_CONTENT_TYPE_NOSNIFF = True

# Proteção contra Clickjacking
X_FRAME_OPTIONS = 'DENY'

# Em produção, forçar cookies seguros
if not DEBUG:
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000  # 1 ano
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True


INSTALLED_APPS = [
    'unfold',  # Django Unfold - Tema moderno do admin
    'unfold.contrib.filters',  # Filtros avançados
    'unfold.contrib.forms',  # Formulários melhorados
    'unfold.contrib.import_export',  # Integração com import_export
    
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    'import_export',  # Biblioteca extra
    
    'portaria',  # Seu App
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

ROOT_URLCONF = 'setup.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'portaria.context_processors.notificacoes',
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
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# Configuração de arquivos de mídia (uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Limite de upload de arquivos (50MB)
DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800
FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_REDIRECT_URL = 'home'
LOGIN_URL = 'login'
LOGOUT_REDIRECT_URL = 'login'

# ==============================================================================
# CONFIGURAÇÕES DO UNFOLD (Visual do Admin)
# ==============================================================================
from django.urls import reverse_lazy

UNFOLD = {
    "SITE_TITLE": "Painel de Administração",
    "SITE_HEADER": "Gestão Condominial",
    "SITE_SUBHEADER": "Painel de Administração",
    "SITE_URL": "/",
    "SITE_SYMBOL": "apartment",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": False,
    "SHOW_BACK_BUTTON": True,
    "BORDER_RADIUS": "8px",
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
                "title": "Condomínios",
                "separator": True,
                "collapsible": True,
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
                ],
            },
            {
                "title": "Moradores & Visitantes",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Moradores",
                        "icon": "groups",
                        "link": reverse_lazy("admin:portaria_morador_changelist"),
                    },
                    {
                        "title": "Visitantes",
                        "icon": "badge",
                        "link": reverse_lazy("admin:portaria_visitante_changelist"),
                    },
                ],
            },
            {
                "title": "Operações",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Encomendas",
                        "icon": "package_2",
                        "link": reverse_lazy("admin:portaria_encomenda_changelist"),
                    },
                    {
                        "title": "Solicitações",
                        "icon": "assignment",
                        "link": reverse_lazy("admin:portaria_solicitacao_changelist"),
                    },
                    {
                        "title": "Avisos",
                        "icon": "campaign",
                        "link": reverse_lazy("admin:portaria_aviso_changelist"),
                    },
                    {
                        "title": "Notificações",
                        "icon": "notifications",
                        "link": reverse_lazy("admin:portaria_notificacao_changelist"),
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
                        "link": reverse_lazy("admin:auth_user_changelist"),
                    },
                    {
                        "title": "Grupos",
                        "icon": "group",
                        "link": reverse_lazy("admin:auth_group_changelist"),
                    },
                ],
            },
            {
                "title": "Links Rápidos",
                "separator": True,
                "collapsible": False,
                "items": [
                    {
                        "title": "Portal do Síndico",
                        "icon": "open_in_new",
                        "link": "/sindico/",
                    },
                    {
                        "title": "Portaria",
                        "icon": "open_in_new",
                        "link": "/",
                    },
                ],
            },
        ],
    },
}
