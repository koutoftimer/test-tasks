import os

os.environ["DJANGO_DEBUG"] = "False"

from .settings import *  # noqa

DEBUG = False

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

REDIS_FAKE = True

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "loggers": {
        "django.request": {
            "handlers": ["null"],
            "propagate": False,
        },
        "likes": {
            "handlers": ["null"],
            "propagate": False,
        },
    },
}
