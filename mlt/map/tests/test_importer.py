import datetime

from django.test import TransactionTestCase

from .utils import create_user



__all__ = ["AddressImporterTest"]



class AddressImporterTest(TransactionTestCase):
    def setUp(self):
        self.user = create_user()


    @property
    def model(self):
        from mlt.map.models import Address
        return Address


    @property
    def importer(self):
        from mlt.map.importer import AddressImporter
        return AddressImporter


    def get_importer(self):
        return self.importer(
            timestamp=datetime.datetime(2011, 7, 8, 1, 2, 3),
            user=self.user,
            source="tests")


    def test_import(self):
        """
        Given an iterable of dictionaries, the process() method saves each
        dictionary as an address, adding the extra importer metadata.

        """

        i = self.get_importer()

        errors = i.process(
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

        self.assertEqual(errors, [])
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
        Errors, if any, are returned as a list of (row-number, ValidationError)
        tuples
        """
        i = self.get_importer()

        errors = i.process(
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
            [(i, e.message_dict) for (i, e) in errors],
            [
                (2, {"state": [u"Value 'NOSUCH' is not a valid choice."]}),
                (3, {"city": [u"This field cannot be blank."]})
                ]
            )
        self.assertEqual(self.model.objects.count(), 0)
