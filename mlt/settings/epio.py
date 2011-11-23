from .prod import *

from bundle_config import config

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": config["postgres"]["database"],
        "USER": config["postgres"]["username"],
        "PASSWORD": config["postgres"]["password"],
        "HOST": config["postgres"]["host"],
    }
}

COMPRESS_OUTPUT_DIR = "cache"

CACHES = {
    "default": {
        "BACKEND": "redis_cache.RedisCache",
        "LOCATION": "{host}:{port}".format(
                host=config["redis"]["host"],
                port=config["redis"]["port"]),
        "OPTIONS": {
            "PASSWORD": config["redis"]["password"],
        },
        "VERSION": config["core"]["version"],
    },
}

CELERY_RESULT_BACKEND = "redis"
CELERY_REDIS_HOST = config["redis"]["host"]
CELERY_REDIS_PORT = config["redis"]["port"]
CELERY_REDIS_PASSWORD = config["redis"]["password"]
CELERY_REDIS_DB = 0

SERVER_EMAIL = "server@provplan.ep.io"
DEFAULT_FROM_EMAIL = "server@provplan.ep.io"
EMAIL_HOST = "mail.threepines.org"
EMAIL_PORT = "587"
EMAIL_USE_TLS = True

SECURE_SSL_HOST = "provplan.ep.io"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTOCOL", "SSL")

MLT_DEFAULT_STATE = "RI"
