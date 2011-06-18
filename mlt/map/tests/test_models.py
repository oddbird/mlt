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
            street_suffix=create_suffix("St"))

        self.assertEqual(a.street, "123 Main St")


    def test_parse_street(self):
        create_suffix("St")
        from mlt.map.addresses import StreetAddress

        self.assertEqual(
            self.model.parse_street("123 N Main St."),
            StreetAddress(number="123", name="N Main", suffix="St")
            )


    def test_parse_streets(self):
        create_suffix("St")
        create_suffix("Ave")
        from mlt.map.addresses import StreetAddress

        self.assertEqual(
            list(self.model.parse_streets(
                    ["123 N Main St.", "567 S Weehawken ave"])),
            [
                StreetAddress(number="123", name="N Main", suffix="St"),
                StreetAddress(number="567", name="S Weehawken", suffix="Ave"),
                ]
            )
