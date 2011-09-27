from mock import Mock

from django.test import TestCase



__all__ = ["BaseWriterTest"]



class BaseWriterTest(TestCase):
    @property
    def writer_class(self):
        from mlt.map.writers.base import BaseWriter
        from mlt.map.serializers import Serializer

        class TestWriter(BaseWriter):
            serializer = Serializer(fields=["one", "two"])

        return TestWriter


    def test_mimetype(self):
        self.assertEqual(self.writer_class.mimetype, "text/plain")


    def test_extension(self):
        self.assertEqual(self.writer_class.extension, "txt")


    def test_field_names(self):
        writer = self.writer_class([])

        self.assertEqual(writer.field_names, ["one", "two"])


    def test_serialized(self):
        ma = Mock()
        ma.one = 1
        ma.two = "two"
        mb = Mock()
        mb.one = "one"
        mb.two = 2

        writer = self.writer_class([ma, mb])

        self.assertEqual(
            list(writer.serialized()),
            [{"one": 1, "two": "two"}, {"one": "one", "two": 2}])


    def test_save_not_implemented(self):
        writer = self.writer_class([])

        with self.assertRaises(NotImplementedError):
            writer.save(None)
