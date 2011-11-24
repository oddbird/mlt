import shutil

from django.db import IntegrityError
from django.test import TestCase

from mock import Mock

from .utils import create_parcel, create_mpolygon, tempdir_shapefile



__all__ = ["LoadParcelsTest"]



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
        shapedir, shapefile = tempdir_shapefile(parcels)
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
        self.func(shapefile, stream=stdout, verbose=True)

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
