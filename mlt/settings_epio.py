from .default_settings import *

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

DEBUG = False
TEMPLATE_DEBUG = False

COMPRESS = True
COMPRESS_OFFLINE = True
COMPRESS_OUTPUT_DIR = "cache"

# nice long randomish string epio gives us
SECRET_KEY = config["redis"]["password"]

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

EMAIL_HOST = "mail.threepines.org"
EMAIL_PORT = "587"
EMAIL_USE_TLS = True
