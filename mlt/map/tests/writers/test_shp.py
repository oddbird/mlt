from cStringIO import StringIO

from django.test import TestCase

from ..utils import create_address, create_parcel



__all__ = ["SHPWriterTest"]



class SHPWriterTest(TestCase):
    @property
    def writer_class(self):
        from mlt.map.writers.shp import SHPWriter
        return SHPWriter


    def test_mimetype(self):
        self.assertEqual(
            self.writer_class.mimetype, "application/shapefile")


    def test_extension(self):
        self.assertEqual(self.writer_class.extension, "shp")


    def test_save(self):
        p1 = create_parcel()

        a1 = create_address(pl=p1.pl)
        a2 = create_address()

        writer = self.writer_class([a1, a2])

        stream = StringIO()
        writer.save(stream)
        stream.seek(0)
