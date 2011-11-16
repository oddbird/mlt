from cStringIO import StringIO
import os.path
import shutil
import tempfile

from django.test import TestCase

from django.contrib.gis.models import SpatialRefSys

from mock import patch
import shapefile

from .utils import create_parcel, create_mpolygon



__all__ = ["LoadParcelsTestCase"]



# maps Parcel attribute names to triple: dbf type, length, dbf field name
parcel_fields = {
    'pl' : ('C', 8, 'PL'),
    'address' : ('C', 27, 'ADD'),
    'first_owner' : ('C', 254, 'FIRST_OWNE'),
    'classcode' : ('C', 55, 'CLASSCODE'),
    }



def write_to_shapefile(parcels):
    """
    Writes given list of parcels to a shapefile that matches the parcel-import
    shapefile. Creates temp directory and dumps shp, shx, dbf, and prj files
    into it; returns tuple (directory-path, shp-file-path).

    Caller is responsible for cleaning up the returned temp directory.

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

    # get SRS info for writing prj file
    srs = SpatialRefSys.objects.get(
        srid=parcels[0]._meta.get_field("geom").srid)

    outdir = tempfile.mkdtemp("mlt-test-shp")

    shp_fn = os.path.join(outdir, "parcels.shp")
    shp = open(shp_fn, "w")
    shx = open(os.path.join(outdir, "parcels.shx"), "w")
    dbf = open(os.path.join(outdir, "parcels.dbf"), "w")
    prj = open(os.path.join(outdir, "parcels.prj"), "w")

    w.save(shp=shp, shx=shx, dbf=dbf)

    prj.write("".join(str(srs).split()))

    shp.close()
    shx.close()
    dbf.close()
    prj.close()

    return (outdir, shp_fn)



class LoadParcelsTestCase(TestCase):
    @property
    def func(self):
        from mlt.map.load import load_parcels
        return load_parcels


    @property
    def model(self):
        from mlt.map.models import Parcel
        return Parcel


    @patch("sys.stdout")
    def test_load(self, stdout):
        p = create_parcel(
            pl="123 45",
            geom=create_mpolygon([
                    (1.0, 2.0),
                    (3.0, 2.0),
                    (3.0, 4.0),
                    (1.0, 4.0),
                    (1.0, 2.0),
                    ]),
            commit=False)

        shapedir, shapefile = write_to_shapefile([p])
        self.addCleanup(shutil.rmtree, shapedir)

        self.func(shapefile)

        stdout.write.assert_called_with("Saved: 123 45\n")

        parcels = self.model.objects.all()

        self.assertEqual(len(parcels), 1)
        parcel = parcels[0]
        self.assertEqual(parcel.geom.coords, p.geom.coords)
        self.assertEqual(parcel.pl, "123 45")


    @patch("sys.stdout")
    def test_second_load(self, stdout):
        create_parcel(pl="135 79")

        p = create_parcel(pl="123 45", commit=False)

        shapedir, shapefile = write_to_shapefile([p])
        self.addCleanup(shutil.rmtree, shapedir)

        self.func(shapefile)

        parcels = self.model.objects.all()

        self.assertEqual(len(parcels), 1)
        self.assertEqual(parcels[0].pl, "123 45")
