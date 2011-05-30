from .base import *

SESSION_COOKIE_SECURE = True
# http://en.wikipedia.org/wiki/Strict_Transport_Security
SECURE_HSTS_SECONDS = 86400
SECURE_FRAME_DENY = True
SECURE_SSL_REDIRECT = True

DEBUG = False
TEMPLATE_DEBUG = False

COMPRESS = True
COMPRESS_OFFLINE = True

COMPRESS_OFFLINE_CONTEXT = {
    "STATIC_URL": STATIC_URL
    }

