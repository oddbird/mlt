from datetime import datetime

from mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from .backports import override_settings
from .utils import create_user, create_address



__all__ = ["AddressFormTest", "AddressImportFormTest"]



class AddressImportFormTest(TestCase):
    def setUp(self):
        self.user = create_user()


    @property
    def form(self):
        from mlt.map.forms import AddressImportForm
        return AddressImportForm


    def test_fields(self):
        self.assertEqual(
            [f.name for f in self.form()],
            ["file", "source"]
            )


    def test_save(self):
        f = self.form(
            data={"source": "mysource"},
            files={"file": SimpleUploadedFile(
                    "data.csv", "123 N Main St, Providence, RI")})

        self.assertTrue(f.is_valid(), f.errors)
        with patch("mlt.map.forms.datetime") as mock:
            mock.utcnow.return_value = datetime(2011, 7, 8, 1, 2, 3)
            self.assertEqual(f.save(self.user), (1, 0))
        from mlt.map.models import Address
        self.assertEqual(Address.objects.count(), 1)
        a = Address.objects.get()
        self.assertEqual(a.imported_by, self.user)
        self.assertEqual(a.import_timestamp, datetime(2011, 7, 8, 1, 2, 3))
        self.assertEqual(a.import_source, "mysource")
        self.assertEqual(a.street, "123 N Main St")
        self.assertEqual(a.city, "Providence")
        self.assertEqual(a.state, "RI")



class AddressFormTest(TestCase):
    @property
    def form(self):
        from mlt.map.forms import AddressForm
        return AddressForm


    @override_settings(MLT_DEFAULT_STATE="SD")
    def test_default_state(self):
        f = self.form()

        self.assertEqual(f.fields["state"].initial, "SD")


    @override_settings(MLT_DEFAULT_STATE=None)
    def test_no_default_state(self):
        f = self.form()

        self.assertEqual(f.fields["state"].initial, None)


    def test_fields(self):
        self.assertEqual(
            [f.name for f in self.form()],
            [
                "street_prefix", "street_number", "street_name", "street_type",
                "street_suffix", "edited_street",
                "city", "state", "multi_units",
                "complex_name", "notes"
                ]
            )


    def test_create(self):
        u = create_user(username="blametern")
        f = self.form(
            {
                "street_number": "3635",
                "street_name": "Van Gordon",
                "street_type": "St",
                "edited_street": "",
                "city": "Providence",
                "state": "RI",
                "multi_units": 1,
                "complex_name": "The Van Gordon Building",
                "notes": "some notes",
                })

        self.assertTrue(f.is_valid())

        with patch("mlt.map.forms.datetime") as mockdt:
            mockdt.utcnow.return_value = datetime(2011, 6, 17, 10, 14, 25)
            a = f.save(u)

        self.assertEqual(a.street_number, "3635")
        self.assertEqual(a.street_name, "Van Gordon")
        self.assertEqual(a.street_type, "St")
        self.assertEqual(a.input_street, "3635 Van Gordon St")
        self.assertEqual(a.parsed_street, "3635 Van Gordon St")
        self.assertEqual(a.edited_street, "")
        self.assertEqual(a.notes, "some notes")
        self.assertEqual(a.complex_name, "The Van Gordon Building")
        self.assertEqual(a.multi_units, True)
        self.assertEqual(a.import_source, "web-ui")
        self.assertEqual(a.imported_by, u)
        self.assertEqual(a.import_timestamp, datetime(2011, 6, 17, 10, 14, 25))


    def test_create_no_street(self):
        f = self.form(
            {
                "street_number": "3635",
                "street_name": "",
                "street_type": "St",
                "edited_street": "",
                "city": "Providence",
                "state": "RI",
                "multi_units": 1,
                "complex_name": "The Van Gordon Building",
                "notes": "some notes",
                })

        self.assertFalse(f.is_valid())
        self.assertEqual(
            f.errors, {'__all__': [u'Please enter a street address.']})


    def test_edit(self):
        u1 = create_user(username="someone")
        a = create_address(
            street_number="1234",
            street_name="Van Heusen",
            street_type="Ave",
            city="Albuquerque",
            state="NM",
            multi_units=False,
            complex_name="",
            notes="",
            imported_by=u1,
            import_source="big batch",
            import_timestamp=datetime(2011, 8, 1, 10, 0, 0))

        u2 = create_user(username="blametern")
        f = self.form(
            {
                "street_number": "3635",
                "street_name": "Van Gordon",
                "street_type": "St",
                "city": "Providence",
                "state": "RI",
                "multi_units": 1,
                "complex_name": "The Van Gordon Building",
                "notes": "some notes",
                },
            instance=a)

        self.assertTrue(f.is_valid())

        a = f.save(u2)

        self.assertEqual(a.street_number, "3635")
        self.assertEqual(a.street_name, "Van Gordon")
        self.assertEqual(a.street_type, "St")
        self.assertEqual(a.input_street, "3635 Van Gordon St")
        self.assertEqual(a.parsed_street, "3635 Van Gordon St")
        self.assertEqual(a.notes, "some notes")
        self.assertEqual(a.complex_name, "The Van Gordon Building")
        self.assertEqual(a.multi_units, True)

        # editing doesn't change these fields
        self.assertEqual(a.import_source, "big batch")
        self.assertEqual(a.imported_by, u1)
        self.assertEqual(a.import_timestamp, datetime(2011, 8, 1, 10, 0, 0))


    def test_edit_unparsed(self):
        u1 = create_user(username="someone")
        a = create_address(
            street_prefix="",
            street_number="",
            street_name="",
            street_type="",
            street_suffix="",
            input_street="123 Main St",
            city="Albuquerque",
            state="NM",
            multi_units=False,
            complex_name="",
            notes="",
            imported_by=u1,
            import_source="big batch",
            import_timestamp=datetime(2011, 8, 1, 10, 0, 0))

        u2 = create_user(username="blametern")
        f = self.form(
            {
                "edited_street": "3635 Van Gordon St",
                "city": "Providence",
                "state": "RI",
                "multi_units": 1,
                "complex_name": "The Van Gordon Building",
                "notes": "some notes",
                },
            instance=a)

        self.assertTrue(f.is_valid())

        a = f.save(u2)

        self.assertEqual(a.street_prefix, "")
        self.assertEqual(a.street_number, "")
        self.assertEqual(a.street_name, "")
        self.assertEqual(a.street_type, "")
        self.assertEqual(a.street_suffix, "")
        self.assertEqual(a.edited_street, "3635 Van Gordon St")
        self.assertEqual(a.input_street, "123 Main St")
        self.assertEqual(a.parsed_street, "")
        self.assertEqual(a.notes, "some notes")
        self.assertEqual(a.complex_name, "The Van Gordon Building")
        self.assertEqual(a.multi_units, True)

        # editing doesn't change these fields
        self.assertEqual(a.import_source, "big batch")
        self.assertEqual(a.imported_by, u1)
        self.assertEqual(a.import_timestamp, datetime(2011, 8, 1, 10, 0, 0))


    def test_edit_no_street(self):
        a = create_address(
            street_prefix="",
            street_number="",
            street_name="",
            street_type="",
            street_suffix="",
            input_street="123 Main St",
            city="Albuquerque",
            state="NM",
            multi_units=False,
            complex_name="",
            notes="",
            )

        f = self.form(
            {
                "street_name": "",
                "edited_street": "",
                "city": "Providence",
                "state": "RI",
                "multi_units": 1,
                "complex_name": "The Van Gordon Building",
                "notes": "some notes",
                },
            instance=a)

        self.assertFalse(f.is_valid())
        self.assertEqual(
            f.errors, {'__all__': [u'Please enter a street address.']})
