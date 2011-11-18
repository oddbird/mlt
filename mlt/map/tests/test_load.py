import os.path
import shutil
import tempfile

from django.db import IntegrityError
from django.test import TestCase

from django.contrib.gis.models import SpatialRefSys

from mock import Mock
import shapefile

from .utils import create_parcel, create_mpolygon



__all__ = ["LoadParcelsTest"]



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



class LoadParcelsTest(TestCase):
    @property
    def func(self):
        from mlt.map.load import load_parcels
        return load_parcels


    @property
    def model(self):
        from mlt.map.models import Parcel
        return Parcel


    def write_shapefile(self, parcels):
        shapedir, shapefile = write_to_shapefile(parcels)
        self.addCleanup(shutil.rmtree, shapedir)
        return shapefile


    def test_load(self):
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

        shapefile = self.write_shapefile([p])

        stdout = Mock()
        self.func(shapefile, stream=stdout)

        stdout.write.assert_called_with("Saved: 123 45\n")

        parcels = self.model.objects.all()

        self.assertEqual(len(parcels), 1)
        parcel = parcels[0]
        self.assertEqual(parcel.geom.coords, p.geom.coords)
        self.assertEqual(parcel.pl, "123 45")


    def test_second_load(self):
        create_parcel(pl="135 79")

        p = create_parcel(pl="123 45", commit=False)

        shapefile = self.write_shapefile([p])

        self.func(shapefile, verbose=False)

        parcels = self.model.objects.all()

        self.assertEqual(len(parcels), 1)
        self.assertEqual(parcels[0].pl, "123 45")



    def test_verbose_false(self):
        shapefile = self.write_shapefile([create_parcel()])

        stdout = Mock()
        self.func(shapefile, verbose=False, stream=stdout)

        self.assertEqual(stdout.write.call_count, 0)


    def test_dupe_pl(self):
        p1 = create_parcel(pl="135 79")
        p2 = create_parcel(pl="135 79")

        shapefile = self.write_shapefile([p1, p2])

        with self.assertRaises(IntegrityError):
            self.func(shapefile, verbose=False, stream=Mock())
