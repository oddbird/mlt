from django.utils.unittest import TestCase



__all__ = ["ParseStreetTest", "SuffixMapTest"]



class ParseStreetTest(TestCase):
    @property
    def func(self):
        from mlt.map.addresses import parse_street
        return parse_street


    @property
    def rv(self):
        from mlt.map.addresses import StreetAddress
        return StreetAddress


    def test_basic(self):
        self.assertEqual(
            self.func("123 N Main St", {"St": "St"}),
            self.rv(number="123", name="N Main", suffix="St")
            )


    def test_initial_whitespace(self):
        self.assertEqual(
            self.func("  123 N Main St", {"St": "St"}),
            self.rv(number="123", name="N Main", suffix="St")
            )


    def test_trailing_whitespace(self):
        self.assertEqual(
            self.func("123 N Main St  ", {"St": "St"}),
            self.rv(number="123", name="N Main", suffix="St")
            )


    def test_trailing_period(self):
        self.assertEqual(
            self.func("123 N Main St.", {"St": "St"}),
            self.rv(number="123", name="N Main", suffix="St")
            )


    def test_alt_suffix(self):
        self.assertEqual(
            self.func("123 N Main Street", {"Street": "St", "St": "St"}),
            self.rv(number="123", name="N Main", suffix="St"))


    def test_suffix_case(self):
        self.assertEqual(
            self.func("123 N Main st", {"St": "St"}),
            self.rv(number="123", name="N Main", suffix="St"))


    def test_pass_suffix_map_object(self):
        from mlt.map.addresses import SuffixMap
        self.assertEqual(
            self.func("123 N Main St", SuffixMap({"St": "St"})),
            self.rv(number="123", name="N Main", suffix="St"))


    def test_no_number(self):
        with self.assertRaises(ValueError) as cm:
            self.func("N Main St", {"St": "St"})

        self.assertEqual(
            str(cm.exception), "No street number found in 'N Main St'")


    def test_no_suffix(self):
        with self.assertRaises(ValueError) as cm:
            self.func("123 N Main", {"St": "St"})

        self.assertEqual(
            str(cm.exception), "No valid suffix found in '123 N Main'")



class SuffixMapTest(TestCase):
    @property
    def cls(self):
        from mlt.map.addresses import SuffixMap
        return SuffixMap


    def test_instantiate_with_suffixmap(self):
        sm = self.cls({"St": "St"})

        # trigger regex compilation
        sm.regex

        sm2 = self.cls(sm)

        self.assertEqual(sm._suffixes, sm2._suffixes)
        self.assertEqual(sm._regex, sm2._regex)


    def test_match(self):
        self.assertEqual(
            self.cls({"St": "St"}).match("something St"),
            ("something", "St"))


    def test_match_returns_canonical(self):
        self.assertEqual(
            self.cls({"Street": "St"}).match("something street"),
            ("something", "St"))


    def test_match_trailing_whitespace(self):
        self.assertEqual(
            self.cls({"St": "St"}).match("something St "),
            ("something", "St"))


    def test_match_trailing_period(self):
        self.assertEqual(
            self.cls({"St": "St"}).match("something St."),
            ("something", "St"))


    def test_match_trailing_period_and_whitespace(self):
        self.assertEqual(
            self.cls({"St": "St"}).match("something St. "),
            ("something", "St"))


    def test_match_case_insensitive(self):
        self.assertEqual(
            self.cls({"St": "St"}).match("something st"),
            ("something", "St"))


    def test_no_match(self):
        self.assertEqual(
            self.cls({"St": "St"}).match("something street"),
            ("something street", None))


    def test_compiled_regex_cached(self):
        sm = self.cls({"St": "St"})

        re1 = sm.regex
        re2 = sm.regex

        self.assertIs(re1, re2)


    def test_getitem(self):
        self.assertEqual(self.cls({"Street": "St"})["Street"], "St")


    def test_getitem_case_insensitive(self):
        self.assertEqual(self.cls({"Street": "St"})["street"], "St")


    def test_get(self):
        self.assertEqual(self.cls({"Street": "St"}).get("Street"), "St")


    def test_get_case_insensitive(self):
        self.assertEqual(self.cls({"Street": "St"}).get("street"), "St")


    def test_get_default(self):
        self.assertEqual(self.cls({"Street": "St"}).get("st", "st"), "st")
