from datetime import datetime

from mock import patch

from django.test import TestCase

from .utils import create_suffix



__all__ = ["AddressFormTest"]



class AddressFormTest(TestCase):
    @property
    def form(self):
        from mlt.map.forms import AddressForm
        return AddressForm


    def create_user(self, username):
        from django.contrib.auth.models import User
        return User.objects.create(username=username)


    def test_fields(self):
        self.assertEqual(
            [f.name for f in self.form()],
            ['city', 'state', 'zip', 'multi_units',
             'complex_name', 'notes', 'street']
            )


    def test_save(self):
        st = create_suffix("St")
        u = self.create_user("blametern")
        f = self.form(
            {
                "street": "3635 Van Gordon St.",
                "city": "Providence",
                "state": "RI",
                "zip": "02909",
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
        self.assertEqual(a.street_suffix, st)
        self.assertEqual(a.zip, "02909")
        self.assertEqual(a.notes, "some notes")
        self.assertEqual(a.complex_name, "The Van Gordon Building")
        self.assertEqual(a.multi_units, True)
        self.assertEqual(a.import_source, "web-ui")
        self.assertEqual(a.imported_by, u)
        self.assertEqual(a.import_timestamp, datetime(2011, 6, 17, 10, 14, 25))


    def test_save_no_number(self):
        create_suffix("St")
        f = self.form(
            {
                "street": "Van Gordon St.",
                "city": "Providence",
                "state": "RI",
                "zip": "02909",
                "multi_units": 1,
                "complex_name": "The Van Gordon Building",
                "notes": "some notes",
                })

        self.assertFalse(f.is_valid())

        self.assertEqual(
            f.errors, {"street": [u"Street address must have a number."]})


    def test_save_no_suffix(self):
        f = self.form(
            {
                "street": "3635 Van Gordon Dr.",
                "city": "Providence",
                "state": "RI",
                "zip": "02909",
                "multi_units": 1,
                "complex_name": "The Van Gordon Building",
                "notes": "some notes",
                })

        self.assertFalse(f.is_valid())

        self.assertEqual(
            f.errors, {"street": [u"Street address must have a valid suffix."]})
