from cStringIO import StringIO
import zipfile

from django.test import TestCase

from mock import patch
import shapefile

from ..utils import create_address, create_parcel, create_mpolygon



__all__ = ["SHPWriterTest"]



class SHPWriterTest(TestCase):
    @property
    def writer_class(self):
        from mlt.map.writers.shp import SHPWriter
        return SHPWriter


    def test_mimetype(self):
        self.assertEqual(
            self.writer_class.mimetype, "application/zip")


    def test_extension(self):
        self.assertEqual(self.writer_class.extension, "zip")


    @patch("mlt.map.writers.shp.DBF_FIELDS", {})
    def test_unrecognized_field(self):
        from mlt.map.writers.shp import dbf_field
        with self.assertRaises(ValueError):
            dbf_field("geocoded")


    def test_save(self):
        p1 = create_parcel(
            geom=create_mpolygon([
                    (1.0, 10.0),
                    (1.0, 20.0),
                    (2.0, 20.0),
                    (2.0, 10.0),
                    (1.0, 10.0),
                    ]))

        a1 = create_address(pl=p1.pl, multi_units=True)
        a2 = create_address()

        writer = self.writer_class([a1, a2])

        stream = StringIO()
        writer.save(stream)
        stream.seek(0)

        z = zipfile.ZipFile(stream, "r")

        self.assertEqual(
            z.namelist(),
            [
                "addresses/addresses.shp",
                "addresses/addresses.shx",
                "addresses/addresses.dbf",
                "addresses/addresses.prj",
                ])

        shp = StringIO(z.open("addresses/addresses.shp").read())
        shx = StringIO(z.open("addresses/addresses.shx").read())
        dbf = StringIO(z.open("addresses/addresses.dbf").read())

        r = shapefile.Reader(shp=shp, shx=shx, dbf=dbf)

        shapes = r.shapeRecords()

        # un-mapped addresses not included at all
        self.assertEqual(len(shapes), 1)

        self.assertEqual(
            [tuple(p) for p in shapes[0].shape.points],
            [
                    (1.0, 10.0),
                    (1.0, 20.0),
                    (2.0, 20.0),
                    (2.0, 10.0),
                    (1.0, 10.0),
                ]
            )

        # "DeletionFlag" makes fields list and records list offset by 1
        self.assertEqual(r.fields[14], ["pl", "C", 8, 0])
        self.assertEqual(shapes[0].record[13], p1.pl)

        self.assertEqual(r.fields[9], ["multi_unit", "L", 1, 0])
        self.assertEqual(shapes[0].record[8], "T")

        z.close()
