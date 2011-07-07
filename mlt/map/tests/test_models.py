from django.test import TestCase

from .utils import create_parcel, create_address, create_mpolygon



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
            sorted(parcel.mapped_to),
            sorted([
                {"street": address1.street, "needs_review": False},
                {"street": address3.street, "needs_review": True},
                ]
                )
            )
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
