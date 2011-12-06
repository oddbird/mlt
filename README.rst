Master Lookup Table
===================

Development
-----------

If you want to run this project in a `virtualenv`_ to isolate it from other
Python projects on your system, create a virtualenv and activate it.  Then
run ``bin/install-reqs`` to install the dependencies for this project into
your Python environment. Python 2.7 is required.

You'll need a PostGIS-enabled PostgreSQL 9.0 database, with the ``citext``
contrib module loaded into it, for this project. See the `GeoDjango
installation documentation`_ for more details on setting up PostGIS and a
PostGIS template database. To enable the ``citext`` module, connect to the
``template_postgis`` database as the Postgres superuser and run ``\i
/usr/share/postgresql/9.0/contrib/citext.sql`` (this is the location of the
``citext.sql`` file on Ubuntu; will vary depending on your Postgres
install). Once you have a PostGIS template database with ``citext`` enabled,
create your database for MLT with a command like ``createdb -T template_postgis
mlt``.

You'll probably need to create an ``mlt/settings/local.py`` file with some
details of your local configuration, including, most likely, your database name
and user (unless they are both named "mlt", the default).  See
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


Importing initial addresses
---------------------------

The MLT includes a user interface for importing batches of addresses from a CSV
file, but this interface can't be used for initially populating the MLT, as the
number of addresses in the initial import is likely too large to complete
within a reasonable time for a web request. In order to manually populate
initial addresses, run ``python manage.py shell`` and then the following
commands in the shell.

This assumes a four-column CSV file, with a header row, with columns for
``pl``, ``street``, ``city``, ``state``. A user is necessary so that the
addresses appear in the changelog as "created"; swap out the username below for
an actual user that you've already created::

    >>> from django.contrib.auth.models import User
    >>> user = User.objects.get(username="example")
    >>> from mlt.map.importer import CSVAddressImporter
    >>> importer = CSVAddressImporter(
    ...     user, fieldnames=["pl", "street", "city", "state"], header=True)
    >>> importer.process_file("/path/to/addresses.csv")


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


JSON API
--------

A simple JSON API is available for querying addresses and batches. The API is
available at the root URL of ``/api/v1/``.


API Keys
~~~~~~~~

Every API call must include the HTTP header ``X-Api-Key``, whose value must be
a valid API key. API keys can be created via the MLT admin interface. An API
call without a valid API key will return an HTTP 403 response, with the
following body::

    {"success": False, "error": "Invalid API key."}


Resource URLs
~~~~~~~~~~~~~

The response to a query to the top-level API URL (``/api/v1/``) will have a
``resource_urls`` key listing the resource URLs available via the
API. Currently these are::

    {
        "resource_urls":
            {
            "addresses": "/api/v1/addresses/",
            "batches": "/api/v1/batches/",
            },
        "success": True,
        }


Result formats
~~~~~~~~~~~~~~

The body of every API response includes a top-level boolean ``success``
key. The value of this key will be true if the request completed successfully;
false if an error occurred. In the latter case the body will also include an
``error`` key describing the nature of the error.

List resource responses will also include a ``total`` key, giving the total
number of resources matching the given filters (even though not all might be
displayed due to paging).


Sorting
~~~~~~~

Every resource list URL can accept one or more sort fields via the ``sort`` key
in the URL querystring. Any field of the returned data for that resource type
can be sorted on; valid fields are listed in the reference for that resource
type. Prepend a ``-`` to the field name to sort descending rather than
ascending on that field. An example multi-field sorted query URL::

    /api/v1/batches/?sort=city&sort=-street


Paging
~~~~~~

All list resources are paged by default, with a default page size of 20
items. Paging is controlled by offset/limit via ``start`` and ``num`` keys in
the URL querystring, rather than by page number. Results will begin with the
``start``-th item, and ``num`` items will be returned. For example, the
following query will return 10 addresses, beginning with the 11th address (in
other words, the second page of size-10 pages)::

    /api/v1/addresses/?start=11&num=10


Filtering
~~~~~~~~~

List resources can be filtered by the value of fields on the resource (see
below for full list of fields for each resource type). Filters are provided in
the URL querystring::

    /api/v1/batches/?tag=foo

Timestamp fields can be filtered on using "[date]" or "[date1] to [date2]",
e.g.::

    /api/v1/batches/?timestamp=11/5/2011+to+11/10/2011


Addresses
~~~~~~~~~

Each address result includes the following fields::

    id
    street
    city
    state
    street_number
    street_prefix
    street_name
    street_type
    street_suffix
    notes
    multi_units
    complex_name
    pl
    mapped_by
    mapped_timestamp
    needs_review
    batches

The ``mapped_by`` field should be sorted/filtered as ``mapped_by__username``,
e.g.::

    /api/v1/addresses/?mapped_by__username=blametern

The ``batches`` field contains a list of batches the address was imported as
part of; each batch will have ``user``, ``timestamp``, and ``tag``
keys. Addresses can be filtered by batch using ``batches__tag``, e.g.::

    /api/v1/addresses/?batches__tag=foo

Addresses can be sorted by latest batch timestamp using
``latest_batch_timestamp``::

    /api/v1/addresses/?sort=latest_batch_timestamp


Batches
~~~~~~~

Each batch includes the following fields::

    timestamp
    tag
    user
    addresses_url

The ``addresses_url`` field is the API URL to get a list of all addresses in
this batch.

The ``user`` field should be sorted or filtered as ``user__username``.
