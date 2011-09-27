from cStringIO import StringIO

from django.test import TestCase


from ..utils import create_address



__all__ = ["CSVWriterTest"]



class CSVWriterTest(TestCase):
    @property
    def writer_class(self):
        from mlt.map.writers.csv import CSVWriter
        return CSVWriter


    def test_save(self):
        a1 = create_address()
        a2 = create_address()

        writer = self.writer_class([a1, a2])

        stream = StringIO()

        writer.save(stream)

        stream.seek(0)

        from mlt.map.serializers import AddressSerializer
        serializer = AddressSerializer()

        def strip_none(d):
            ret = {}
            for k, v in d.items():
                if v is None:
                    v = ""
                ret[k] = v
            return ret

        self.assertEqual(
            stream.read(),
            "id,street,street_prefix,street_number,street_name,street_type,street_suffix,multi_units,city,state,complex_name,notes,pl,mapped_by,mapped_timestamp,needs_review,imported_by,import_timestamp,import_source,latitude,longitude\r\n" +
            "%(id)s,%(street)s,%(street_prefix)s,%(street_number)s,%(street_name)s,%(street_type)s,%(street_suffix)s,%(multi_units)s,%(city)s,%(state)s,%(complex_name)s,%(notes)s,%(pl)s,%(mapped_by)s,%(mapped_timestamp)s,%(needs_review)s,%(imported_by)s,%(import_timestamp)s,%(import_source)s,%(latitude)s,%(longitude)s\r\n" % strip_none(serializer.one(a1)) +
            "%(id)s,%(street)s,%(street_prefix)s,%(street_number)s,%(street_name)s,%(street_type)s,%(street_suffix)s,%(multi_units)s,%(city)s,%(state)s,%(complex_name)s,%(notes)s,%(pl)s,%(mapped_by)s,%(mapped_timestamp)s,%(needs_review)s,%(imported_by)s,%(import_timestamp)s,%(import_source)s,%(latitude)s,%(longitude)s\r\n" % strip_none(serializer.one(a2))
            )
