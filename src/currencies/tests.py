import datetime
from decimal import Decimal

from django.test import TestCase

from currencies.choices import currency_choices
from currencies.exchange import exchange
from currencies.formatting import render_amount
from currencies.models import ExchangeRate


class ExchangeTestCase(TestCase):
    date = datetime.date(2021, 12, 31)

    def setUp(self):
        ExchangeRate.objects.create(
            date=self.date, base_currency="EUR", currency="USD", rate=1.1326
        )
        ExchangeRate.objects.create(
            date=self.date, base_currency="EUR", currency="ZAR", rate=18.0625
        )

    def test_can_echange_from_base(self):
        self.assertEqual(exchange(1, "EUR", "USD", date=self.date), Decimal("1.13"))

    def test_can_echange_to_base(self):
        self.assertEqual(exchange(1, "USD", "EUR", date=self.date), Decimal("0.88"))

    def test_can_echange_through_base(self):
        self.assertEqual(exchange(1, "USD", "ZAR", date=self.date), Decimal("15.95"))

    def test_uses_last_valid_rate(self):
        self.assertEqual(
            exchange(1, "EUR", "USD", date=datetime.date(2022, 1, 1)), Decimal("1.13")
        )


class CurrencyChoicesTestCase(TestCase):
    def test_expected_contents(self):
        currencies = currency_choices()
        self.assertIn(("EUR", "EUR (Euro)"), currencies)
        self.assertIn(("USD", "USD (US Dollar)"), currencies)
        self.assertIn(("ZAR", "ZAR (Rand)"), currencies)

    def test_skips_x_currencies(self):
        codes = [code for code, name in currency_choices()]
        self.assertNotIn("XTS", codes)
        self.assertNotIn("XXX", codes)
        self.assertIn("XCD", codes)

    def test_can_include_x_currencies(self):
        codes = [code for code, name in currency_choices(exclude_special=False)]
        self.assertIn("XTS", codes)
        self.assertIn("XXX", codes)
        self.assertIn("XCD", codes)


class CurrencyRenderTestCase(TestCase):
    def test_renders_rand(self):
        self.assertEqual(render_amount(Decimal(1000), "ZAR"), "1000.00 ZAR")

    def test_renders_yen(self):
        self.assertEqual(render_amount(Decimal(1000), "JPY"), "1000 JPY")
