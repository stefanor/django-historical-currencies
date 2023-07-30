import datetime

from django.test import TestCase

from historical_currencies.models import ExchangeRate, check_fresh_exchange_rate_data


class CurrencyFreshnessCheckTestCase(TestCase):
    def test_fails_when_exchange_data_is_stale(self):
        errors = check_fresh_exchange_rate_data(None)
        self.assertEqual(len(errors), 1)
        error = errors[0]
        self.assertEqual(error.level, 40)
        self.assertEqual(error.msg, "no current exchange rates")

    def test_passes_when_exchange_data_is_fresh(self):
        date = datetime.date.today()
        ExchangeRate.objects.create(
            date=date, base_currency="EUR", currency="USD", rate=1.1326
        )
        errors = check_fresh_exchange_rate_data(None)
        self.assertEqual(errors, [])
