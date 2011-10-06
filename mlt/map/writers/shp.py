from cStringIO import StringIO
import zipfile

from django.db import models

from django.contrib.auth.models import User
from django.contrib.gis.models import SpatialRefSys

import shapefile

from ..models import Address, Parcel
from ..serializers import AddressSerializer
from .base import AddressWriter


# DBF field types: "C" character, "N" numeric, "L" logical (boolean)
# types for fields that can't be introspected, or overrides:
DBF_FIELDS = {
    "id": ("N", 32),
    "street_is_parsed": ("L", 1),
    "latitude": ("N", 32),
    "longitude": ("N", 32),
    }

DBF_C_MAX = 254 # maximum recommended length for DBF char field

def dbf_field(field_name):
    """
    For a given Address field name, returns a tuple of (dbf_type, size), where
    dbf_type is "C" for character, "N" for numeric, or "L" for logical.

    """
    ret = DBF_FIELDS.get(field_name)
    if ret is not None:
        return ret
    fld = Address._meta.get_field(field_name, many_to_many=False)
    if isinstance(fld, models.CharField):
        return ("C", min(fld.max_length, DBF_C_MAX))
    if isinstance(fld, models.TextField):
        return ("C", DBF_C_MAX)
    if isinstance(fld, models.BooleanField):
        return ("L", 1)
    if isinstance(fld, models.DateTimeField):
        return ("C", 26) # length of ISO format datetime
    if isinstance(fld, models.ForeignKey) and fld.rel.to is User:
        return ("C", 30) # length of User.username field
    raise ValueError("Field name %r is not recognized." % field_name)



class ShapefileAddressSerializer(AddressSerializer):
    def _encode_boolean(self, val):
        "pyshp coerces False to empty string, we need to avoid that."
        return str(val)[0]


    def encode_multi_units(self, val):
        return self._encode_boolean(val)


    def encode_needs_review(self, val):
        return self._encode_boolean(val)


    def encode_street_is_parsed(self, val):
        return self._encode_boolean(val)



class SHPWriter(AddressWriter):
    mimetype = "application/zip"
    extension = "zip"

    serializer = ShapefileAddressSerializer()


    def save(self, stream):
        w = shapefile.Writer()

        # create DBF fields for all properties
        for field_name in self.field_names:
            field_type, size = dbf_field(field_name)
            w.field(field_name, field_type, size)

        # for each mapped address, create polygon and record
        for address in self.objects:
            if address.parcel:
                serialized = self.serializer.one(address)
                w.poly(parts=sum(address.parcel.geom.coords, ()))
                w.record(**serialized)

        # get SRS info for writing prj file
        srs = SpatialRefSys.objects.get(
            srid=Parcel._meta.get_field("geom").srid)

        shp = StringIO()
        shx = StringIO()
        dbf = StringIO()
        prj = StringIO()

        w.save(shp=shp, shx=shx, dbf=dbf)

        prj.write("".join(str(srs).split()))

        shp.seek(0)
        shx.seek(0)
        dbf.seek(0)
        prj.seek(0)

        z = zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED)

        z.writestr("addresses/addresses.shp", shp.read())
        z.writestr("addresses/addresses.shx", shx.read())
        z.writestr("addresses/addresses.dbf", dbf.read())
        z.writestr("addresses/addresses.prj", prj.read())

        z.close()
