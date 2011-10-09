#!/usr/bin/env python
"""
Runs a Django management command.

Avoids the double-settings-import and extra sys.path additions of Django's
default manage.py.

"""
import os, sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mlt.settings.base")

from django.core.management import execute_from_command_line

execute_from_command_line(sys.argv)
