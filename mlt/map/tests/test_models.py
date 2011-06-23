from django.test import TestCase

from .utils import create_address, create_suffix, create_alias



__all__ = ["StreetSuffixTest", "AddressTest"]



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
