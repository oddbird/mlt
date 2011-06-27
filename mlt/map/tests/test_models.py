from django.test import TestCase

from .utils import (
    create_parcel, create_address, create_suffix, create_alias, create_mpolygon)



__all__ = ["ParcelTest", "StreetSuffixTest", "AddressTest"]



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



class StreetSuffixTest(TestCase):
    @property
    def model(self):
        from mlt.map.models import StreetSuffix
        return StreetSuffix


    def test_create_suffix_map(self):
        create_alias("Street", create_suffix("St"))
        create_suffix("Ave")

        sm = self.model.suffix_map()

        from mlt.map.addresses import SuffixMap
        self.assertIsInstance(sm, SuffixMap)
        self.assertEqual(
            sm._suffixes, {"st": "St", "street": "St", "ave": "Ave"})



class AddressTest(TestCase):
    @property
    def model(self):
        from mlt.map.models import Address
        return Address


    def test_street_property(self):
        a = create_address(
            street_number="123",
            street_name="Main",
            street_suffix="St")

        self.assertEqual(a.street, "123 Main St")


    def test_street_property_unparsed(self):
        a = create_address(
            input_street="123 Main St",
            street_number="",
            street_name="",
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
