import datetime
from cStringIO import StringIO

from django.test import TransactionTestCase

from mock import patch

from .utils import create_user, create_address



__all__ = ["AddressImporterTest", "CSVAddressImporterTest"]



class GetImporterMixin(object):
    def setUp(self):
        self.user = create_user()


    @property
    def importer(self):
        raise NotImplementedError


    def get_importer(self, **kwargs):
        defaults = dict(
            timestamp=datetime.datetime(2011, 7, 8, 1, 2, 3),
            user=self.user,
            tag="tests")
        defaults.update(kwargs)
        return self.importer(**defaults)



class AddressImporterTest(GetImporterMixin, TransactionTestCase):
    @property
    def model(self):
        from mlt.map.models import Address
        return Address


    @property
    def importer(self):
        from mlt.map.importer import AddressImporter
        return AddressImporter


    @property
    def ImporterError(self):
        from mlt.map.importer import ImporterError
        return ImporterError


    def test_import(self):
        """
        Given  an iterable  of dictionaries,  the process()  method  saves each
        dictionary as an address, adding batch metadata, returning the count of
        addresses added and the count of dupes.

        """

        i = self.get_importer()

        create_address(
            input_street="3815 Brookside Dr", city="Rapid City", state="SD")

        count, dupes = i.process(
            [
                {
                    "street": "123 N Main St",
                    "city": "Rapid City",
                    "state": "SD"
                    },
                {
                    "street": "3815 Brookside Dr",
                    "city": "Rapid City",
                    "state": "SD"
                    },
                ]
            )

        self.assertEqual(count, 1)
        self.assertEqual(dupes, 1)
        self.assertEqual(
            set([a.input_street for a in self.model.objects.all()]),
            set(["123 N Main St", "3815 Brookside Dr"])
            )

        batches = self.model._meta.get_field("batches").rel.to.objects.all()
        self.assertEqual(len(batches), 1)
        batch = batches[0]
        self.assertEqual(batch.user, self.user)
        self.assertEqual(batch.tag, "tests")
        self.assertEqual(
            batch.timestamp, datetime.datetime(2011, 7, 8, 1, 2, 3))
        self.assertEqual(
            [list(a.batches.all()) for a in self.model.objects.all()],
            [[batch], [batch]]
            )


    def test_import_errors(self):
        """
        Errors, if any, are raised as an ImporterError whose ``errors``
        attribute is a list of (row-number, error-dict) tuples.

        """
        i = self.get_importer()

        with self.assertRaises(self.ImporterError) as cm:
            i.process(
                [
                    {
                        "street": "123 N Main St",
                        "city": "Rapid City",
                        "state": "SD"
                        },
                    {
                        "street": "3815 Brookside Dr",
                        "city": "Rapid City",
                        "state": "NOSUCH"
                        },
                    {
                        "street": "3815 Brookside Dr",
                        "state": "SD"
                        },
                    ]
                )

        self.assertEqual(
            cm.exception.errors,
            [
                (2, {"state": [u"Value 'NOSUCH' is not a valid choice."]}),
                (3, {"city": [u"This field cannot be blank."]})
                ]
            )
        self.assertEqual(self.model.objects.count(), 0)


    def test_bad_field_name(self):
        i = self.get_importer()

        with self.assertRaises(self.ImporterError) as cm:
            i.process(
                [
                    {
                        "street": "123 Main St",
                        "city": "Providence",
                        "state": "RI",
                        "foo": "bar",
                        }
                    ]
                )

        self.assertEqual(
            cm.exception.errors,
            [
                (1, {"?": [u"Extra or unknown columns in input."]})
                ]
            )


    def test_none_in_data(self):
        i = self.get_importer()

        with self.assertRaises(self.ImporterError) as cm:
            i.process(
                [
                    {
                        "street": "123 Main St",
                        "city": "Providence",
                        "state": "RI",
                        None: ["yo"],
                        }
                    ]
                )

        self.assertEqual(
            cm.exception.errors,
            [
                (1, {"?": [u"Extra or unknown columns in input."]})
                ]
            )


    def test_unexpected_error(self):
        """
        An unexpected error rolls back the transaction and is re-raised.

        """
        i = self.get_importer()

        with patch("mlt.map.importer.Address.objects.create_from_input") as ci:
            class SomeError(Exception):
                pass
            def raise_someerror(*args, **kwargs):
                raise SomeError()
            ci.side_effect = raise_someerror
            with self.assertRaises(SomeError):
                i.process([{}])



class CSVAddressImporterTest(AddressImporterTest):
    @property
    def importer(self):
        from mlt.map.importer import CSVAddressImporter
        return CSVAddressImporter


    def test_process_file(self):
        i = self.get_importer()

        fh = StringIO(
            "123 N Main St, Rapid City, SD\n3815 Brookside, Rapid City, SD")

        count, dupes = i.process_file(fh)

        self.assertEqual(count, 2)
        self.assertEqual(dupes, 0)
        self.assertEqual(
            [a.input_street for a in self.model.objects.all()],
            ["123 N Main St", "3815 Brookside"])


    def test_custom_fields(self):
        i = self.get_importer(fieldnames=["pl", "street", "city", "state"])

        fh = StringIO(
            "123 51,123 N Main St, Rapid City, SD\n"
            "123 52, 3815 Brookside, Rapid City, SD")

        count, dupes = i.process_file(fh)

        self.assertEqual(count, 2)
        self.assertEqual(dupes, 0)
        self.assertEqual(
            [a.pl for a in self.model.objects.all()],
            ["123 51", "123 52"])


    def test_extra_fields(self):
        i = self.get_importer()

        fh = StringIO(
            "123 N Main St, Rapid City, SD, some, extra, columns\n"
            "3815 Brookside, Rapid City, SD, more, extra, data")

        count, dupes = i.process_file(fh)

        self.assertEqual(count, 2)


    def test_header(self):
        i = self.get_importer(header=True)

        fh = StringIO(
            "street, city, state\n"
            "123 N Main St, Rapid City, SD\n"
            "3815 Brookside, Rapid City, SD")

        count, dupes = i.process_file(fh)

        self.assertEqual(count, 2)
        self.assertEqual(dupes, 0)
