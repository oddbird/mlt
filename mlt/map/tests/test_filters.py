from datetime import datetime, timedelta

from django.utils.unittest import TestCase



__all__ = ["GetDateSuggestTest", "ParseDateRangeTest"]



class GetDateSuggestTest(TestCase):
    @property
    def func(self):
        from mlt.map.filters import get_date_suggest
        return get_date_suggest


    def test_empty(self):
        self.assertEqual(self.func(""), None)


    def test_no_parse(self):
        self.assertEqual(self.func("b"), None)


    def test_just_date(self):
        self.assertEqual(
            self.func("8/31"),
            {"q": "8/31", "full": "8/31 to [date]", "rest": " to [date]"})


    def test_date_plus(self):
        self.assertEqual(
            self.func("8/31 to "),
            {"q": "8/31 to ", "full": "8/31 to [date]", "rest": "[date]"})


    def test_date_plus_some(self):
        self.assertEqual(
            self.func("8/31 t"),
            {"q": "8/31 t", "full": "8/31 to [date]", "rest": "o [date]"})


    def test_date_plus_junk_ending_in_o(self):
        self.assertEqual(self.func("8/31 go"), None)



class ParseDateRangeTest(TestCase):
    @property
    def func(self):
        from mlt.map.filters import parse_date_range
        return parse_date_range

    @property
    def today(self):
        return datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0)

    def test_empty(self):
        self.assertEqual(self.func(""), None)


    def test_too_few_bits(self):
        self.assertEqual(self.func("b"), None)


    def test_too_many_bits(self):
        self.assertEqual(self.func("1 to 3 to 5"), None)


    def test_bad_bits(self):
        self.assertEqual(self.func("8/31 to foo"), None)


    def test_success(self):
        self.assertEqual(
            self.func("8/31/11 to 9/5/11"),
            (datetime(2011, 8, 31), datetime(2011, 9, 5))
            )


    def test_blank_today(self):
        self.assertEqual(
            self.func("to 9/5/11"),
            (self.today, datetime(2011, 9, 5))
            )
        self.assertEqual(
            self.func("9/5/11 to"),
            (datetime(2011, 9, 5), self.today)
            )


    def test_today(self):
        self.assertEqual(
            self.func("today to 9/5/11"),
            (self.today, datetime(2011, 9, 5))
            )
        self.assertEqual(
            self.func("9/5/11 to today"),
            (datetime(2011, 9, 5), self.today)
            )


    def test_yesterday(self):
        yest = self.today - timedelta(days=1)
        self.assertEqual(
            self.func("yesterday to 9/5/11"),
            (yest, datetime(2011, 9, 5))
            )
        self.assertEqual(
            self.func("9/5/11 to  yesterday"),
            (datetime(2011, 9, 5), yest)
            )


    def test_tomorrow(self):
        tomorrow = self.today + timedelta(days=1)
        self.assertEqual(
            self.func("tomorrow  to 9/5/11"),
            (tomorrow, datetime(2011, 9, 5))
            )
        self.assertEqual(
            self.func("9/5/11 to tomorrow"),
            (datetime(2011, 9, 5), tomorrow)
            )
