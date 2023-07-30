import datetime
from io import StringIO

from django.core.management import call_command
from django.test import TestCase, tag

from historical_currencies.models import ExchangeRate


@tag("internet")
class ECBImportTestCase(TestCase):
    def test_ecb_daily_import(self):
        last_week = datetime.date.today() - datetime.timedelta(days=7)
        rates = ExchangeRate.objects.filter(
            currency="USD", base_currency="EUR", date__gte=last_week
        )
        self.assertFalse(rates.exists())
        out = StringIO()
        call_command("import_ecb_exchangerates", "--daily", stdout=out)
        self.assertTrue(rates.exists())
