from cStringIO import StringIO
from datetime import datetime
import os.path
import tempfile
import zipfile

from django.contrib.gis.models import SpatialRefSys

import shapefile



def refresh(obj):
    return obj.__class__._base_manager.get(pk=obj.pk)



user_number = 1

def create_user(**kwargs):
    global user_number

    password = kwargs.pop("password", None)
    if "username" not in kwargs:
        kwargs["username"] = "test%s" % user_number
        user_number += 1

    from django.contrib.auth.models import User

    user = User(**kwargs)
    if password:
        user.set_password(password)
    user.save()
    return user



def create_mpolygon(points):
    return (
        "MULTIPOLYGON(((%s)))" %
        ", ".join([" ".join([str(lat), str(lng)]) for lat, lng in points]))



def create_parcel(**kwargs):
    commit = kwargs.pop("commit", True)
    defaults = {
        "pl": "111 22",
        "address": "3635 Van Gordon St",
        "first_owner": "Van Gordon",
        "classcode": "Single Family Residence",
        "geom": create_mpolygon([
            ("-71.4057922808270291", "41.7882712655665784"),
            ("-71.4059239736763516", "41.7882228772817541"),
            ("-71.4060543071226732", "41.7884215532894530"),
            ("-71.4059226139629004", "41.7884699426220294"),
            ("-71.4057922808270291", "41.7882712655665784"),
            ]),
        "import_timestamp": datetime.now(),
        }
    defaults.update(kwargs)

    from mlt.map.models import Parcel
    if commit:
        return Parcel.objects.create(**defaults)
    else:
        return Parcel(**defaults)



def create_suffix(suffix="St"):
    from mlt.map.models import StreetSuffix
    return StreetSuffix.objects.get_or_create(suffix=suffix)[0]



def create_alias(alias="Street", suffix=None):
    if suffix is None:
        suffix = create_suffix("St")

    from mlt.map.models import StreetSuffixAlias
    return StreetSuffixAlias.objects.get_or_create(
        alias=alias, suffix=suffix)[0]



def create_address(**kwargs):
    defaults = {
        "input_street": "3635 Van Gordon St",
        "city": "Providence",
        "state": "RI",
        }
    defaults.update(kwargs)

    user = defaults.pop("user", create_user())

    from mlt.map.models import Address
    a = Address(**defaults)
    a.save(user=user)
    return a


def create_address_batch(**kwargs):
    defaults = {
        "timestamp": datetime.now(),
        "tag": "testing",
        }

    defaults.update(kwargs)
    if "user" not in defaults:
        defaults["user"] = create_user()

    from mlt.map.models import AddressBatch
    return AddressBatch.objects.create(**defaults)



# maps Parcel attribute names to triple: dbf type, length, dbf field name
parcel_fields = {
    'pl' : ('C', 8, 'PL'),
    'address' : ('C', 27, 'ADD'),
    'first_owner' : ('C', 254, 'FIRST_OWNE'),
    'classcode' : ('C', 55, 'CLASSCODE'),
    }



def write_to_shapefile(parcels, shp, shx, dbf):
    """
    Writes given list of parcels to shapefile represented by the three given
    streams ``shp``, ``shx``, and ``dbf``, which must be writable streams.

    """
    w = shapefile.Writer()

    # create DBF fields for all properties
    for dbf_type, dbf_size, dbf_name in parcel_fields.values():
        w.field(dbf_name, dbf_type, dbf_size)

    # for each parcel, create polygon and record
    for parcel in parcels:
        dbf_data = {}
        for attname, (_, _, dbf_name) in parcel_fields.items():
            dbf_data[dbf_name] = getattr(parcel, attname)
        w.poly(parts=sum(parcel.geom.coords, ()))
        w.record(**dbf_data)

    w.save(shp=shp, shx=shx, dbf=dbf)



def tempdir_shapefile(parcels):
    """
    Writes given list of parcels to a shapefile that matches the parcel-import
    shapefile. Creates temp directory and dumps shp, shx, dbf, and prj files
    into it; returns tuple (directory-path, shp-file-path).

    Caller is responsible for cleaning up the returned temp directory.

    """

    outdir = tempfile.mkdtemp("mlt-test-shp")

    shp_fn = os.path.join(outdir, "parcels.shp")
    shp = open(shp_fn, "w")
    shx = open(os.path.join(outdir, "parcels.shx"), "w")
    dbf = open(os.path.join(outdir, "parcels.dbf"), "w")
    prj = open(os.path.join(outdir, "parcels.prj"), "w")

    write_to_shapefile(parcels, shp=shp, shx=shx, dbf=dbf)

    # get SRS info for writing prj file
    srs = SpatialRefSys.objects.get(
        srid=parcels[0]._meta.get_field("geom").srid)

    prj.write("".join(str(srs).split()))

    shp.close()
    shx.close()
    dbf.close()
    prj.close()

    return (outdir, shp_fn)



def zip_shapefile(parcels):
    """
    Writes given list of parcels to a shapefile that matches the parcel-import
    shapefile. Creates in-memory zip file and dumps shp, shx, dbf, and prj
    files into it; returns zip-file buffer.

    """
    shp = StringIO()
    shx = StringIO()
    dbf = StringIO()
    prj = StringIO()

    write_to_shapefile(parcels, shp=shp, shx=shx, dbf=dbf)

    # get SRS info for writing prj file
    srs = SpatialRefSys.objects.get(
        srid=parcels[0]._meta.get_field("geom").srid)

    prj.write("".join(str(srs).split()))

    shp.seek(0)
    shx.seek(0)
    dbf.seek(0)
    prj.seek(0)

    out = StringIO()

    z = zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED)

    z.writestr("parcels/parcels.shp", shp.read())
    z.writestr("parcels/parcels.shx", shx.read())
    z.writestr("parcels/parcels.dbf", dbf.read())
    z.writestr("parcels/parcels.prj", prj.read())

    z.close()

    out.seek(0)
    return out
