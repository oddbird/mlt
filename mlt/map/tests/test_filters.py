from datetime import datetime, timedelta

from django.utils.unittest import TestCase



__all__ = ["ParseDateTest", "ParseDateRangeTest"]



class ParseDateTest(TestCase):
    @property
    def func(self):
        from mlt.map.filters import parse_date
        return parse_date


    @property
    def today(self):
        return datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0)


    def test_trailing_slash(self):
        self.assertEqual(
            self.func("8/11/"), self.today.replace(day=11, month=8))


    def test_trailing_dash(self):
        self.assertEqual(
            self.func("8-11-"), self.today.replace(day=11, month=8))


    def test_today(self):
        self.assertEqual(self.func("today"), self.today)


    def test_yesterday(self):
        self.assertEqual(
            self.func("yesterday "), self.today - timedelta(days=1))


    def test_tomorrow(self):
        self.assertEqual(
            self.func(" tomorrow"), self.today + timedelta(days=1))



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


    def test_single_day(self):
        self.assertEqual(
            self.func("8/31/11"),
            (datetime(2011, 8, 31), datetime(2011, 8, 31))
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
