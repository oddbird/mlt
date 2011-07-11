import datetime

from django.core.exceptions import ValidationError
from django.test import TestCase

from .utils import create_parcel, create_address, create_mpolygon, create_user



__all__ = ["ParcelTest", "AddressTest"]



class ParcelTest(TestCase):
    @property
    def model(self):
        from mlt.map.models import Parcel
        return Parcel


    def test_latitude(self):
        parcel = create_parcel(
            geom=create_mpolygon([
                    (1.0, 5.0),
                    (1.0, 9.0),
                    (3.0, 9.0),
                    (3.0, 5.0),
                    (1.0, 5.0)]))

        self.assertEqual(parcel.latitude, 7.0)


    def test_longitude(self):
        parcel = create_parcel(
            geom=create_mpolygon([
                    (1.0, 5.0),
                    (1.0, 9.0),
                    (3.0, 9.0),
                    (3.0, 5.0),
                    (1.0, 5.0)]))

        self.assertEqual(parcel.longitude, 2.0)


    def test_mapped(self):
        parcel = create_parcel(pl="1234")
        address1 = create_address(pl="1234", needs_review=False)
        create_address(pl="12345")
        address3 = create_address(pl="1234", needs_review=True)
        parcel2 = create_parcel(pl="4321")

        self.assertEqual(
            set(parcel.mapped_addresses), set([address1, address3]))
        self.assertEqual(
            set([a["pl"] for a in parcel.mapped_to]), set(["1234"]))
        self.assertTrue(parcel.mapped)
        self.assertFalse(parcel2.mapped)



class AddressTest(TestCase):
    @property
    def model(self):
        from mlt.map.models import Address
        return Address


    def test_parsed_street(self):
        a = create_address(
            street_number="123",
            street_name="Main",
            street_type="St")

        self.assertEqual(a.parsed_street, "123 Main St")


    def test_street_property(self):
        a = create_address(
            street_number="123",
            street_name="Main",
            street_type="St")

        self.assertEqual(a.street, "123 Main St")


    def test_street_property_unparsed(self):
        a = create_address(
            input_street="123 Main St",
            street_prefix="",
            street_number="",
            street_name="",
            street_type="",
            street_suffix="",
            )

        self.assertEqual(a.street, "123 Main St")


    def test_parcel_property(self):
        a = create_address(pl="11 222")
        p = create_parcel(pl="11 222")

        self.assertEqual(a.parcel, p)


    def test_parcel_property_no_such_pl(self):
        a = create_address(pl="11 222")

        self.assertEqual(a.parcel, None)


    def test_parcel_property_no_pl(self):
        a = create_address(pl="")

        self.assertEqual(a.parcel, None)


    def import_data(self):
        try:
            user = self._import_user
        except AttributeError:
            user = self._import_user = create_user()

        return {
            "import_timestamp": datetime.datetime(2011, 7, 8, 1, 2, 3),
            "imported_by": user,
            "import_source": "tests",
            }


    def create_from_input(self, **kwargs):
        data = self.import_data()
        data.update(kwargs)
        return self.model.objects.create_from_input(**data)


    def test_create(self):
        a = create_address(
            input_street="123 N Main St", city="Rapid City", state="SD")

        b = self.create_from_input(
            street="321 S Little St", city="Rapid City", state="SD")

        self.assertNotEqual(a, b)
        self.assertEqual(b.input_street, "321 S Little St")


    def test_create_dupe(self):
        create_address(
            input_street="123 N Main St", city="Rapid City", state="SD")

        b = self.create_from_input(
            street="123 N Main St", city="Rapid City", state="SD")


        self.assertIs(b, None)
        self.assertEqual(self.model.objects.count(), 1)


    def test_create_dupe_different_case(self):
        create_address(
            input_street="123 N Main St", city="Rapid City", state="SD")

        b = self.create_from_input(
            street="123 n main st", city="rapid city", state="sd")


        self.assertIs(b, None)


    def test_create_dupe_whitespace(self):
        create_address(
            input_street="123 N Main St", city="Rapid City", state="SD")

        b = self.create_from_input(
            street="123 n main st  ", city=" rapid city", state="  sd")


        self.assertIs(b, None)


    def test_create_dupe_of_parsed(self):
        create_address(
            input_street="123  N Main St.",
            street_number="123", street_name="N Main", street_type="St",
            city="Rapid City", state="SD")

        b = self.create_from_input(
            street="123 N Main St", city="Rapid City", state="SD")


        self.assertIs(b, None)


    def test_create_uppercases_state(self):
        a = self.create_from_input(
            street="321 S Little St", city="Rapid City", state="sd")

        self.assertEqual(a.state, "SD")


    def test_create_strips_whitespace(self):
        a = self.create_from_input(
            street="321 S Little St", city=" Rapid City", state=" SD ")

        self.assertEqual(a.state, "SD")


    def test_create_bad_data(self):
        with self.assertRaises(ValidationError):
            self.create_from_input(
                street="123 N Main St", city="Rapid City", state="NOSUCH")


    def test_create_no_state(self):
        with self.assertRaises(ValidationError):
            self.create_from_input(
                street="123 N Main St", city="Rapid City")


    def test_create_no_street(self):
        with self.assertRaises(ValidationError):
            self.create_from_input(city="Rapid City", state="SD")
