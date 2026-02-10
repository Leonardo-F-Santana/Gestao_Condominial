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
# CONFIGURAÇÕES DO JAZZMIN (Visual do Admin)
# ==============================================================================
JAZZMIN_SETTINGS = {
    "site_title": "Portaria Inteligente",
    "site_header": "Gestão Condominial",
    "site_brand": "Condomínio Admin",
    "welcome_sign": "Bem-vindo ao Painel de Controle",
    "copyright": "Portaria Inteligente Ltda",
    
    "show_sidebar": True,
    "navigation_expanded": True,
    
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "portaria.Visitante": "fas fa-user-clock",
        "portaria.Encomenda": "fas fa-box-open",
        "portaria.Morador": "fas fa-home",
        "portaria.Solicitacao": "fas fa-clipboard-list",
    },
    
    "order_with_respect_to": [
        "portaria", 
        "portaria.Solicitacao", 
        "portaria.Encomenda", 
        "portaria.Visitante", 
        "portaria.Morador", 
        "auth"
    ],

    "custom_links": {
        "portaria": [{
            "name": "💻 Abrir Sistema da Portaria", 
            "url": "home", 
            "icon": "fas fa-laptop-house",
        }]
    },
    
    "topmenu_links": [
        {"name": "Ir para Portaria", "url": "home", "permissions": ["auth.view_user"]},
        {"model": "auth.User"},
    ],
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-primary",
    "accent": "accent-primary",
    "navbar": "navbar-dark navbar-primary",
    "no_navbar_border": False,
    "navbar_fixed": False,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "flatly", 
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}