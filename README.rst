Master Lookup Table
===================

Development
-----------

If you want to run this project in a `virtualenv`_ to isolate it from other
Python projects on your system, create a virtualenv and activate it.  Then
run ``bin/install-reqs`` to install the dependencies for this project into
your Python environment. Python 2.7 is required.

You'll need a PostGIS-enabled PostgreSQL database available for this
project; create it with a command like ``createdb -T template_postgis mlt``. 
See the `GeoDjango installation documentation`_ for more details on setting
up PostGIS and a PostGIS template database.

You'll probably need to create an ``mlt/settings/local.py`` file with some
details of your local configuration, including, most likely, your database
name and user (unless they are both named "mlt").  See
``mlt/settings/local.sample.py`` for a sample that can be copied to
``mlt/settings/local.py`` and modified.

Once this configuration is done, you should be able to run ``./manage.py
syncdb --migrate``, then ``./manage.py runserver`` and access the MLT in
your browser at ``http://localhost:8000``.

.. _virtualenv: http://www.virtualenv.org
.. _GeoDjango installation documentation: http://docs.djangoproject.com/en/1.3/ref/contrib/gis/install/

To install the necessary Ruby Gems for Compass/Sass development, run
``bin/install-gems requirements/gems.txt``.  Update
``requirements/gems.txt`` if newer gems should be used.

Deployment
----------

In addition to the above configuration, in any production deployment this
entire app should be served exclusively over HTTPS (since almost all use of the
site is authenticated, and serving authenticated pages over HTTP invites
session hijacking attacks). Ideally, the non-HTTP URLs should redirect to the
HTTPS version. The ``SESSION_COOKIE_SECURE`` setting should be set to ``True``
in ``settings_local.py`` when the app is being served over HTTPS.

This app also uses the new `staticfiles contrib app`_ in Django 1.3 for
collecting static assets from reusable components into a single directory
for production serving.  Under "runserver" in development this is handled
automatically.  In production, run ``./manage.py collectstatic`` to collect
all static assets into the ``collected-assets`` directory (or whatever
``STATIC_ROOT`` is set to in ``settings_local.py``), and make those
collected assets available by HTTP at the ``STATIC_URL`` setting.

.. _staticfiles contrib app: http://docs.djangoproject.com/en/1.3/howto/static-files/
