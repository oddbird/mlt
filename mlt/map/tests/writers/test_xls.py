from cStringIO import StringIO

from django.test import TestCase

import xlrd

from ..utils import create_address



__all__ = ["XLSWriterTest"]



class XLSWriterTest(TestCase):
    @property
    def writer_class(self):
        from mlt.map.writers.xls import XLSWriter
        return XLSWriter


    def test_mimetype(self):
        self.assertEqual(self.writer_class.mimetype, "application/vnd.ms-excel")


    def test_extension(self):
        self.assertEqual(self.writer_class.extension, "xls")


    def test_save(self):
        a1 = create_address()
        a2 = create_address()

        writer = self.writer_class([a1, a2])

        stream = StringIO()

        writer.save(stream)

        stream.seek(0)

        workbook = xlrd.open_workbook(file_contents=stream.read())

        self.assertEqual(workbook.nsheets, 1)

        sheet = workbook.sheet_by_index(0)

        self.assertEqual(sheet.name, "Addresses")
        self.assertEqual(sheet.nrows, 3)
        self.assertEqual(sheet.ncols, 23)
