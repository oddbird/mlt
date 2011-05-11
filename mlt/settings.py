import os

from .default_settings import *

local_settings = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "settings_local.py"))

if os.path.exists(local_settings):
    exec(open(local_settings).read())


COMPRESS_ROOT = STATIC_ROOT
COMPRESS_URL = STATIC_URL
