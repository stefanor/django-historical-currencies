import datetime

from django.test import SimpleTestCase

from historical_currencies.models import ExchangeRate


class ExchangeRateObjectTestCase(SimpleTestCase):
    def test_str_method(self):
        er = ExchangeRate(
            date=datetime.date(2021, 12, 31),
            base_currency="EUR",
            currency="USD",
            rate=1.1326,
        )
        self.assertEqual(str(er), "Exchange Rate: EUR-USD @ 2021-12-31: 1.1326")
