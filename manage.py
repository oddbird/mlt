#!/usr/bin/env python
"""
Runs a Django management command.

Avoids the double-settings-import and extra sys.path additions of Django's
default manage.py.

"""
import os, sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mlt.settings.base")
    os.environ.setdefault("CELERY_LOADER", "djcelery.loaders.DjangoLoader")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
