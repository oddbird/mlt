from datetime import datetime

from mock import patch

from django.test import TestCase



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
            [
                "street_number", "street_name", "street_suffix",
                "city", "state", "multi_units",
                "complex_name", "notes"
                ]
            )


    def test_save(self):
        u = self.create_user("blametern")
        f = self.form(
            {
                "street_number": "3635",
                "street_name": "Van Gordon",
                "street_suffix": "St",
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
        self.assertEqual(a.street_suffix, "St")
        self.assertEqual(a.input_street, "3635 Van Gordon St")
        self.assertEqual(a.parsed_street, "3635 Van Gordon St")
        self.assertEqual(a.notes, "some notes")
        self.assertEqual(a.complex_name, "The Van Gordon Building")
        self.assertEqual(a.multi_units, True)
        self.assertEqual(a.import_source, "web-ui")
        self.assertEqual(a.imported_by, u)
        self.assertEqual(a.import_timestamp, datetime(2011, 6, 17, 10, 14, 25))

