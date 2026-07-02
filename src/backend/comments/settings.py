import os
import re
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "django-insecure-dev-key")
DEBUG = os.environ.get("DJANGO_DEBUG", "True") == "True"
ALLOWED_HOSTS = os.environ.get(
    "DJANGO_ALLOWED_HOSTS", "api.comments,localhost,127.0.0.1"
).split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "djoser",
    "corsheaders",
    "captcha",
    "comments",
    "attachments",
    "accounts",
    "likes",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

if DEBUG:
    INSTALLED_APPS.append("silk")
    MIDDLEWARE.insert(
        MIDDLEWARE.index("django.middleware.security.SecurityMiddleware") + 1,
        "silk.middleware.SilkyMiddleware",
    )
    # see: https://silk.readthedocs.io/en/latest/configuration.html#meta-profiling
    SILKY_META = True

ROOT_URLCONF = "comments.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "comments.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "comments"),
        "USER": os.environ.get("POSTGRES_USER", "comments"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "comments"),
        "HOST": os.environ.get("POSTGRES_HOST", "db"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
        # see: https://docs.djangoproject.com/en/6.0/ref/databases/#transaction-pooling-and-server-side-cursors
        "DISABLE_SERVER_SIDE_CURSORS": True,
    }
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "static"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"
API_BASE_URL = os.environ.get("API_BASE_URL", "http://api.comments:8002").rstrip("/")

REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
REDIS_DB = int(os.environ.get("REDIS_DB", "0"))

MASTER_CAPTCHA_VALUE = os.environ.get("MASTER_CAPTCHA_VALUE", "")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# DRF
REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "comments.pagination.CommentsPagination",
    "PAGE_SIZE": 25,
    "DEFAULT_RENDERER_CLASSES": [
        "comments.renderers.FastJSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.MultiPartParser",
        "rest_framework.parsers.FormParser",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
}

if DEBUG:
    REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"].append(
        "rest_framework.renderers.BrowsableAPIRenderer",
    )


# JWT
def _parse_duration(value):
    match = re.match(
        r"^(\d+)\s*(minute|min|m|hour|h|day|d)s?$", value.strip(), re.IGNORECASE
    )
    if not match:
        raise ValueError(f"Invalid duration: {value}")
    num = int(match.group(1))
    unit = match.group(2).lower()
    units = {
        "minute": "minutes",
        "min": "minutes",
        "m": "minutes",
        "hour": "hours",
        "h": "hours",
        "day": "days",
        "d": "days",
    }
    return timedelta(**{units[unit]: num})


SIMPLE_JWT = {
    "AUTH_HEADER_TYPES": ("Bearer",),
    "ACCESS_TOKEN_LIFETIME": _parse_duration(
        os.environ.get("JWT_ACCESS_TOKEN_LIFETIME", "5 minutes")
    ),
    "REFRESH_TOKEN_LIFETIME": _parse_duration(
        os.environ.get("JWT_REFRESH_TOKEN_LIFETIME", "1 day")
    ),
}

# Djoser
DJOSER = {
    "LOGIN_FIELD": "username",
    "USER_CREATE_PASSWORD_RETYPE": False,
    "SERIALIZERS": {
        "user": "accounts.serializers.UserSerializer",
        "current_user": "accounts.serializers.UserSerializer",
    },
}

# CORS
CORS_ALLOW_ALL_ORIGINS = DEBUG

default_cors = [
    "http://dev.comments:5173",
    "http://web.comments:8002",
    "http://localhost:5173",
]
CORS_ALLOWED_ORIGINS = (
    os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",")
    if os.environ.get("CORS_ALLOWED_ORIGINS")
    else default_cors
)

# Captcha
CAPTCHA_CHALLENGE_FUNCT = "captcha.helpers.random_char_challenge"
CAPTCHA_NOISE_FUNCTIONS = ("captcha.helpers.noise_dots",)
CAPTCHA_FONT_SIZE = 28
CAPTCHA_IMAGE_SIZE = (200, 60)
CAPTCHA_LENGTH = 4

# File uploads
MAX_IMAGE_SIZE = (320, 240)
MAX_AVATAR_SIZE = (24, 24)
MAX_TEXT_FILE_SIZE = 100 * 1024

# Allowed HTML tags
ALLOWED_HTML_TAGS = {
    "a": ["href", "title"],
    "br": [],
    "code": [],
    "i": [],
    "img": ["src", "alt", "width", "height"],
    "p": [],
    "strong": [],
}

# Add this to ensure CSRF works with the cross-domain setup
CSRF_TRUSTED_ORIGINS = (
    os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",")
    if os.environ.get("CSRF_TRUSTED_ORIGINS")
    else default_cors
)

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    # 1. Define how logs should look
    "formatters": {
        "verbose": {
            "format": "{asctime} {module} {levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",  # Apply the formatter here
        },
    },
    "loggers": {
        # Your app logic
        "likes": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        # CRITICAL: Captures 500 errors and Django system warnings
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        # Optional: Captures SQL if you set level to DEBUG (useful for profiling)
        "django.db.backends": {
            "handlers": ["console"],
            "level": "INFO",  # Change to DEBUG to see every SQL query
            "propagate": False,
        },
    },
}
