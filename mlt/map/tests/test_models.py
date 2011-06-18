from django.test import TestCase



__all__ = ["StreetSuffixTest", "AddressTest"]



class StreetSuffixTest(TestCase):
    @property
    def model(self):
        from mlt.map.models import StreetSuffix
        return StreetSuffix


    def _load(self):
        st = self.model.objects.create(suffix="St")
        self.model.objects.create(suffix="Ave")

        st.aliases.create(alias="Street")


    def test_create_suffix_map(self):
        self._load()

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


    def _load_suffixes(self):
        from mlt.map.models import StreetSuffix

        st = StreetSuffix.objects.create(suffix="St")
        StreetSuffix.objects.create(suffix="Ave")

        st.aliases.create(alias="Street")


    def test_parse_street(self):
        self._load_suffixes()
        from mlt.map.addresses import StreetAddress

        self.assertEqual(
            self.model.parse_street("123 N Main St."),
            StreetAddress(number="123", name="N Main", suffix="St")
            )


    def test_parse_streets(self):
        self._load_suffixes()
        from mlt.map.addresses import StreetAddress

        self.assertEqual(
            list(self.model.parse_streets(
                    ["123 N Main St.", "567 S Weehawken ave"])),
            [
                StreetAddress(number="123", name="N Main", suffix="St"),
                StreetAddress(number="567", name="S Weehawken", suffix="Ave"),
                ]
            )
