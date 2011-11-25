from cStringIO import StringIO
from xml.etree import ElementTree

from django.test import TestCase

from ..utils import create_address, create_parcel



__all__ = ["KMLWriterTest"]



class KMLWriterTest(TestCase):
    @property
    def writer_class(self):
        from mlt.map.writers.kml import KMLWriter
        return KMLWriter


    def test_mimetype(self):
        self.assertEqual(
            self.writer_class.mimetype, "application/vnd.google-earth.kml+xml")


    def test_extension(self):
        self.assertEqual(self.writer_class.extension, "kml")


    def test_save(self):
        p1 = create_parcel()

        a1 = create_address(pl=p1.pl)
        a2 = create_address()

        writer = self.writer_class([a1, a2])

        stream = StringIO()
        count = writer.save(stream)
        stream.seek(0)

        self.assertEqual(count, 2)

        kml = stream.read()

        tree = ElementTree.fromstring(kml)

        placemarks = list(tree)

        self.assertEqual(len(placemarks), 2, kml)
        # name, ExtendedData, MultiGeometry
        self.assertEqual(len(placemarks[0]), 3, kml)
        # no parcel so no geometry
        self.assertEqual(len(placemarks[1]), 2, kml)
