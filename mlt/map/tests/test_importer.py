import datetime
from cStringIO import StringIO

from django.test import TransactionTestCase

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
            source="tests")
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


    def test_import(self):
        """
        Given an iterable of dictionaries, the process() method saves each
        dictionary as an address, adding the extra importer metadata, returning
        the count of addresses added and the count of dupes.

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
        self.assertEqual(
            self.model.objects.values(
                "import_timestamp", "imported_by", "import_source").distinct()[0],
            {
                'import_timestamp': datetime.datetime(2011, 7, 8, 1, 2, 3),
                'imported_by': int(self.user.id),
                'import_source': u'tests',
                }
            )


    def test_import_errors(self):
        """
        Errors, if any, are raised as an ImporterError whose ``errors``
        attribute is a list of (row-number, error-dict) tuples.

        """
        from mlt.map.importer import ImporterError

        i = self.get_importer()

        with self.assertRaises(ImporterError) as cm:
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
