from datetime import timedelta
from pathlib import Path
import os
import environ

# Initialize environment variables
env = environ.Env()

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent
environ.Env.read_env(BASE_DIR / ".env")

# -----------------------------------------------------------------------------
# General Settings
# -----------------------------------------------------------------------------
SECRET_KEY = env("SECRET_KEY")  # Keep this secret in production
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

# -----------------------------------------------------------------------------
# Installed Applications
# -----------------------------------------------------------------------------
INSTALLED_APPS = [
    # Admin extensions
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "unfold.contrib.inlines",
    "unfold.contrib.guardian",

    # Django built-in apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party apps
    "debug_toolbar",
    "rest_framework",
    "django_filters",
    "djoser",
    "drf_spectacular",
    "health_check",
    "health_check.db",
    "health_check.cache",
    "health_check.storage",
    "health_check.contrib.migrations",
    "colorfield",
    "guardian",

    # Local apps
    "car_companion",
    "authentication",
]

# -----------------------------------------------------------------------------
# Middleware
# -----------------------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",  # Only in debug mode
]

# -----------------------------------------------------------------------------
# URL and WSGI Configuration
# -----------------------------------------------------------------------------
ROOT_URLCONF = "core.urls"
WSGI_APPLICATION = "core.wsgi.application"

# -----------------------------------------------------------------------------
# Templates
# -----------------------------------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
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

# -----------------------------------------------------------------------------
# Database
# -----------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": env("DB_ENGINE"),
        "NAME": env("DB_NAME"),
        "HOST": env("DB_HOST"),
        "PORT": env("DB_PORT"),
        "USER": env("DB_USER"),
        "PASSWORD": env("DB_PASSWORD"),
    }
}

# -----------------------------------------------------------------------------
# Authentication
# -----------------------------------------------------------------------------
AUTH_USER_MODEL = "authentication.CustomUser"
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",  # Default
    "guardian.backends.ObjectPermissionBackend",  # For object-level permissions
]

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# -----------------------------------------------------------------------------
# Internationalization and Localization
# -----------------------------------------------------------------------------
LANGUAGE_CODE = env("LANGUAGE_CODE", default="en-us")
TIME_ZONE = env("TIME_ZONE", default="UTC")
USE_I18N = env.bool("USE_I18N", default=True)
USE_TZ = env.bool("USE_TZ", default=True)

# -----------------------------------------------------------------------------
# Static and Media Files
# -----------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")

# -----------------------------------------------------------------------------
# REST Framework and JWT
# -----------------------------------------------------------------------------
REST_FRAMEWORK = {
    "COERCE_DECIMAL_TO_STRING": False,
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SIMPLE_JWT = {
    "AUTH_HEADER_TYPES": ("JWT",),
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
}

# -----------------------------------------------------------------------------
# Djoser Configuration
# -----------------------------------------------------------------------------
DJOSER = {
    "SEND_ACTIVATION_EMAIL": True,
    "SEND_CONFIRMATION_EMAIL": True,
    "ACTIVATION_URL": "api/auth/users/activation/{uid}/{token}",
    "PASSWORD_RESET_CONFIRM_URL": "api/auth/users/reset_password_confirm/{uid}/{token}",
    "EMAIL": {
        "activation": "authentication.emails.ActivationEmail",
        "password_reset": "authentication.emails.PasswordResetEmail",
        "confirmation": "authentication.emails.ConfirmationEmail",
    },
    "SERIALIZERS": {
        "user_create": "authentication.serializers.UserRegistrationSerializer",  # Custom serializer
    },
    "PROTOCOL": "https",
}

# -----------------------------------------------------------------------------
# Email Settings
# -----------------------------------------------------------------------------
SITE_NAME = env("SITE_NAME")
EMAIL_BACKEND = env("EMAIL_BACKEND")
EMAIL_HOST = env("EMAIL_HOST")
EMAIL_PORT = env.int("EMAIL_PORT")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_USE_SSL = env.bool("EMAIL_USE_SSL", default=False)
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
EMAIL_TIMEOUT = env.int("EMAIL_TIMEOUT", default=5)


# -----------------------------------------------------------------------------
# Debug Toolbar
# -----------------------------------------------------------------------------
INTERNAL_IPS = ["127.0.0.1"]

# -----------------------------------------------------------------------------
# OpenAPI and Documentation
# -----------------------------------------------------------------------------
SPECTACULAR_SETTINGS = {
    "TITLE": "Car Companion API",
    "DESCRIPTION": "API for Car Companion project",
    "VERSION": "1.0.0",
}

# -----------------------------------------------------------------------------
# Unfold Configuration
# -----------------------------------------------------------------------------
UNFOLD = {
    "SITE_TITLE": "Car Companion",
    "SITE_HEADER": "Car Companion",
    "SITE_URL": "/",
    "SITE_ICON": None,  # Add your icon path if needed
}

# -----------------------------------------------------------------------------
# Default Primary Key Field Type
# -----------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
